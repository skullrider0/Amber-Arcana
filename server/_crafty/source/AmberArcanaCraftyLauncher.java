import java.io.*;
import java.lang.management.ManagementFactory;
import java.net.URI;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class AmberArcanaCraftyLauncher {
    static final String MC = "1.20.1";
    static final String FORGE = "47.4.10";
    static final String FORGE_COORD = MC + "-" + FORGE;
    static final Path ROOT = Paths.get("").toAbsolutePath().normalize();
    static final HttpClient HTTP = HttpClient.newBuilder()
            .followRedirects(HttpClient.Redirect.ALWAYS)
            .connectTimeout(Duration.ofSeconds(30))
            .build();
    static volatile Process child;

    record Mod(String fileId, String filename, String sha512, String slug, String name) {}

    public static void main(String[] args) throws Exception {
        System.out.println("[Amber & Arcana] Crafty bootstrap starting in " + ROOT);
        System.out.println("[Amber & Arcana] Minecraft " + MC + " / Forge " + FORGE);
        Files.createDirectories(ROOT.resolve("mods"));
        cleanupRemovedMods();
        cleanupReplacedRecipeViewers();
        List<Mod> mods = readMods(ROOT.resolve("_crafty/server-mods.tsv"));
        downloadMods(mods);
        installForgeIfNeeded();
        launchForge(args);
    }

    static void cleanupRemovedMods() throws IOException {
        Path list = ROOT.resolve("_crafty/remove-mods.txt");
        if (!Files.isRegularFile(list)) return;
        for (String line : Files.readAllLines(list, StandardCharsets.UTF_8)) {
            String name = line.trim();
            if (name.isBlank() || name.startsWith("#")) continue;
            Path target = ROOT.resolve("mods").resolve(name).normalize();
            if (!target.getParent().equals(ROOT.resolve("mods"))) continue;
            if (Files.deleteIfExists(target)) {
                System.out.println("[Amber & Arcana] Removed server-incompatible/client-only mod: " + name);
            }
        }
    }

    static void cleanupReplacedRecipeViewers() throws IOException {
        Path modsDir = ROOT.resolve("mods");
        Set<String> pinned = new HashSet<>();
        for (Mod mod : readMods(ROOT.resolve("_crafty/server-mods.tsv"))) pinned.add(mod.filename());
        for (String pattern : List.of("jei-*.jar", "polymorph-*.jar", "RoughlyEnoughItems-*.jar", "REIPluginCompatibilities-*.jar")) {
            try (DirectoryStream<Path> stream = Files.newDirectoryStream(modsDir, pattern)) {
                for (Path jar : stream) {
                    if (pinned.contains(jar.getFileName().toString())) continue;
                    Files.deleteIfExists(jar);
                    System.out.println("[Amber & Arcana] Removed replaced/server-side recipe viewer: " + jar.getFileName());
                }
            }
        }
    }

    static List<Mod> readMods(Path p) throws IOException {
        List<Mod> out = new ArrayList<>();
        for (String line : Files.readAllLines(p, StandardCharsets.UTF_8)) {
            if (line.isBlank() || line.startsWith("#")) continue;
            String[] x = line.split("\\t", 5);
            if (x.length != 5) throw new IOException("Invalid mod entry: " + line);
            out.add(new Mod(x[0], x[1], x[2], x[3], x[4]));
        }
        return out;
    }

    static void downloadMods(List<Mod> mods) throws Exception {
        System.out.println("[Amber & Arcana] Checking " + mods.size() + " dedicated-server mod files...");
        int threads = Math.min(6, Math.max(2, Runtime.getRuntime().availableProcessors() / 2));
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        AtomicInteger done = new AtomicInteger();
        List<Future<?>> futures = new ArrayList<>();
        for (Mod m : mods) {
            futures.add(pool.submit(() -> {
                try {
                    Path dest = ROOT.resolve("mods").resolve(m.filename());
                    if (Files.isRegularFile(dest) && verifyHash(dest, m.sha512())) {
                        int n = done.incrementAndGet();
                        System.out.printf("[mods %d/%d] OK %s%n", n, mods.size(), m.filename());
                        return;
                    }
                    if (Files.exists(dest)) Files.delete(dest);
                    downloadCurseForge(m, dest);
                    if (!verifyHash(dest, m.sha512())) {
                        Files.deleteIfExists(dest);
                        throw new IOException("Checksum mismatch after download: " + m.filename());
                    }
                    int n = done.incrementAndGet();
                    System.out.printf("[mods %d/%d] DOWNLOADED %s%n", n, mods.size(), m.filename());
                } catch (Exception e) {
                    throw new CompletionException(e);
                }
            }));
        }
        pool.shutdown();
        List<Throwable> failures = new ArrayList<>();
        for (Future<?> f : futures) {
            try { f.get(); }
            catch (ExecutionException e) { failures.add(e.getCause()); }
        }
        if (!failures.isEmpty()) {
            System.err.println("[Amber & Arcana] One or more mod downloads failed:");
            for (Throwable t : failures) System.err.println("  - " + t.getMessage());
            throw new IOException("Failed to prepare " + failures.size() + " mod file(s). See errors above.");
        }
    }

    static void downloadCurseForge(Mod m, Path dest) throws Exception {
        String id = m.fileId();
        if (id.length() <= 3) throw new IOException("Unexpected CurseForge file ID: " + id);
        String a = id.substring(0, id.length() - 3);
        String b = id.substring(id.length() - 3);
        String encoded = encodePathSegment(m.filename());
        String path = "/files/" + a + "/" + b + "/" + encoded;
        String[] hosts = {"mediafilez.forgecdn.net", "edge.forgecdn.net", "media.forgecdn.net"};
        Exception last = null;
        for (String host : hosts) {
            Path part = dest.resolveSibling(dest.getFileName() + ".part");
            Files.deleteIfExists(part);
            try {
                URI uri = URI.create("https://" + host + path);
                HttpRequest req = HttpRequest.newBuilder(uri)
                        .timeout(Duration.ofMinutes(5))
                        .header("User-Agent", "AmberArcana-Crafty4-ServerBootstrap/1.0")
                        .GET().build();
                HttpResponse<Path> res = HTTP.send(req, HttpResponse.BodyHandlers.ofFile(part));
                if (res.statusCode() >= 200 && res.statusCode() < 300 && Files.size(part) > 0) {
                    try {
                        Files.move(part, dest, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
                    } catch (AtomicMoveNotSupportedException ex) {
                        Files.move(part, dest, StandardCopyOption.REPLACE_EXISTING);
                    }
                    return;
                }
                Files.deleteIfExists(part);
                last = new IOException("HTTP " + res.statusCode() + " from " + host);
            } catch (Exception e) {
                Files.deleteIfExists(part);
                last = e;
            }
        }
        throw new IOException(m.filename() + " (CurseForge file " + m.fileId() + ") failed from all CDN hosts", last);
    }

    static String encodePathSegment(String s) {
        StringBuilder out = new StringBuilder();
        for (byte bb : s.getBytes(StandardCharsets.UTF_8)) {
            int c = bb & 0xff;
            if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.' || c == '~') {
                out.append((char)c);
            } else {
                out.append('%');
                char[] hex = "0123456789ABCDEF".toCharArray();
                out.append(hex[(c >> 4) & 15]).append(hex[c & 15]);
            }
        }
        return out.toString();
    }

    static boolean verifyHash(Path p, String expected) throws Exception {
        if (expected == null || expected.isBlank()) return Files.isRegularFile(p) && Files.size(p) > 0;
        String value = expected.trim();
        String algorithm = "SHA-512";
        if (value.regionMatches(true, 0, "sha1:", 0, 5)) {
            algorithm = "SHA-1";
            value = value.substring(5);
        }
        MessageDigest md = MessageDigest.getInstance(algorithm);
        try (InputStream in = Files.newInputStream(p)) {
            byte[] buf = new byte[1024 * 1024];
            for (int n; (n = in.read(buf)) > 0;) md.update(buf, 0, n);
        }
        StringBuilder sb = new StringBuilder();
        for (byte b : md.digest()) sb.append(String.format("%02x", b));
        return sb.toString().equalsIgnoreCase(value);
    }

    static void installForgeIfNeeded() throws Exception {
        Path unixArgs = ROOT.resolve("libraries/net/minecraftforge/forge/" + FORGE_COORD + "/unix_args.txt");
        if (Files.isRegularFile(unixArgs)) {
            System.out.println("[Amber & Arcana] Forge installation already present.");
            return;
        }
        Path installerDir = ROOT.resolve("_crafty/installer");
        Files.createDirectories(installerDir);
        Path installer = installerDir.resolve("forge-" + FORGE_COORD + "-installer.jar");
        if (!Files.isRegularFile(installer) || Files.size(installer) < 100_000) {
            System.out.println("[Amber & Arcana] Downloading Forge installer...");
            URI uri = URI.create("https://maven.minecraftforge.net/net/minecraftforge/forge/" + FORGE_COORD + "/forge-" + FORGE_COORD + "-installer.jar");
            HttpRequest req = HttpRequest.newBuilder(uri).timeout(Duration.ofMinutes(5))
                    .header("User-Agent", "AmberArcana-Crafty4-ServerBootstrap/1.0").GET().build();
            Path part = installer.resolveSibling(installer.getFileName() + ".part");
            Files.deleteIfExists(part);
            HttpResponse<Path> res = HTTP.send(req, HttpResponse.BodyHandlers.ofFile(part));
            if (res.statusCode() < 200 || res.statusCode() >= 300) {
                Files.deleteIfExists(part);
                throw new IOException("Forge installer download failed: HTTP " + res.statusCode());
            }
            Files.move(part, installer, StandardCopyOption.REPLACE_EXISTING);
        }
        System.out.println("[Amber & Arcana] Installing Forge " + FORGE_COORD + " server files...");
        List<String> cmd = List.of(forgeJavaCommand(), "-jar", installer.toString(), "--installServer");
        Process p = new ProcessBuilder(cmd).directory(ROOT.toFile()).inheritIO().start();
        int rc = p.waitFor();
        if (rc != 0 || !Files.isRegularFile(unixArgs)) {
            throw new IOException("Forge installer failed with exit code " + rc);
        }
        System.out.println("[Amber & Arcana] Forge installation complete.");
    }

    static void launchForge(String[] appArgs) throws Exception {
        List<String> cmd = new ArrayList<>();
        String forgeJava = forgeJavaCommand();
        cmd.add(forgeJava);
        // Spark stays available for manual diagnostics. Background profiling is disabled by config;
        // retain the Java sampler override as an additional safety fallback.
        cmd.add("-Dspark.backgroundProfilerEngine=java");
        // Amber & Arcana 0.1.9-5 safe memory preset. Crafty often defaults imports to 4096 MB,
        // which is too small for this pack. The bootstrap process itself can stay small; the real
        // Forge child is always launched with the pack preset below.
        cmd.add("-Xms4096M");
        cmd.add("-Xmx10240M");
        for (String a : ManagementFactory.getRuntimeMXBean().getInputArguments()) {
            // Preserve Crafty/JVM tuning flags, but not inherited heap sizes: the pack preset owns those.
            if (a.startsWith("-XX:")) cmd.add(a);
        }
        cmd.add("@libraries/net/minecraftforge/forge/" + FORGE_COORD + "/unix_args.txt");
        // The Crafty import passes nogui. Preserve any non-launcher application args too.
        boolean hasNogui = false;
        for (String a : appArgs) {
            if (a.equalsIgnoreCase("nogui")) hasNogui = true;
            cmd.add(a);
        }
        if (!hasNogui) cmd.add("nogui");
        System.out.println("[Amber & Arcana] Forge Java: " + forgeJava);
        System.out.println("[Amber & Arcana] Spark background profiler engine: java (native async-profiler disabled)");
        System.out.println("[Amber & Arcana] Forge heap preset: Xms=4096 MB / Xmx=10240 MB");
        System.out.println("[Amber & Arcana] Launching Forge dedicated server...");
        child = new ProcessBuilder(cmd).directory(ROOT.toFile()).inheritIO().start();
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            Process c = child;
            if (c != null && c.isAlive()) {
                c.destroy();
                try { c.waitFor(10, TimeUnit.SECONDS); } catch (InterruptedException ignored) {}
                if (c.isAlive()) c.destroyForcibly();
            }
        }, "amber-arcana-forge-shutdown"));
        int rc = child.waitFor();
        System.out.println("[Amber & Arcana] Forge exited with code " + rc);
        System.exit(rc);
    }

    static String javaCommand() {
        return ProcessHandle.current().info().command().orElse("java");
    }

    static String forgeJavaCommand() {
        LinkedHashSet<String> candidates = new LinkedHashSet<>();

        String explicit = System.getenv("AMBER_ARCANA_JAVA17");
        if (explicit != null && !explicit.isBlank()) candidates.add(explicit.trim());

        for (String env : new String[]{"JAVA17_HOME", "JDK17_HOME"}) {
            String home = System.getenv(env);
            if (home != null && !home.isBlank()) {
                candidates.add(Paths.get(home, "bin", "java").toString());
            }
        }

        // Common Debian/Ubuntu/Crafty Java 17 locations.
        candidates.add("/usr/lib/jvm/java-17-openjdk-amd64/bin/java");
        candidates.add("/usr/lib/jvm/java-17-openjdk/bin/java");
        candidates.add("/usr/lib/jvm/temurin-17-jdk-amd64/bin/java");
        candidates.add("/usr/lib/jvm/temurin-17-jre-amd64/bin/java");

        // Crafty detects installed JVMs through update-alternatives on Linux too.
        try {
            Process p = new ProcessBuilder("update-alternatives", "--list", "java")
                    .redirectErrorStream(true).start();
            try (BufferedReader r = p.inputReader(StandardCharsets.UTF_8)) {
                for (String line; (line = r.readLine()) != null;) {
                    if (!line.isBlank()) candidates.add(line.trim());
                }
            }
            p.waitFor(5, TimeUnit.SECONDS);
        } catch (Exception ignored) {}

        // Also scan /usr/lib/jvm in case alternatives is unavailable.
        Path jvmRoot = Paths.get("/usr/lib/jvm");
        if (Files.isDirectory(jvmRoot)) {
            try (var stream = Files.walk(jvmRoot, 4)) {
                stream.filter(x -> x.getFileName() != null && x.getFileName().toString().equals("java"))
                        .filter(x -> x.getParent() != null && x.getParent().getFileName() != null && x.getParent().getFileName().toString().equals("bin"))
                        .forEach(x -> candidates.add(x.toString()));
            } catch (IOException ignored) {}
        }

        // Prefer the exact runtime Crafty launched us with if it is already Java 17.
        candidates.add(javaCommand());

        for (String candidate : candidates) {
            if (isJava17(candidate)) {
                System.out.println("[Amber & Arcana] Selected Java 17 runtime: " + candidate);
                return candidate;
            }
        }

        String fallback = javaCommand();
        System.err.println("[Amber & Arcana] WARNING: Java 17 was not found. Falling back to: " + fallback);
        System.err.println("[Amber & Arcana] For Minecraft 1.20.1 / Forge 47.4.10, select Java 17 in Crafty if available.");
        return fallback;
    }

    static boolean isJava17(String java) {
        if (java == null || java.isBlank()) return false;
        try {
            Path pth = Paths.get(java);
            if (java.contains(File.separator) && !Files.isExecutable(pth)) return false;
            Process p = new ProcessBuilder(java, "-version").redirectErrorStream(true).start();
            String text;
            try (InputStream in = p.getInputStream()) {
                text = new String(in.readAllBytes(), StandardCharsets.UTF_8).toLowerCase(Locale.ROOT);
            }
            if (!p.waitFor(5, TimeUnit.SECONDS)) {
                p.destroyForcibly();
                return false;
            }
            return text.contains("version \"17.") || text.contains("version \"17\"");
        } catch (Exception ignored) {
            return false;
        }
    }
}
