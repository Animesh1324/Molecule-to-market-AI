/** @type {import('next').NextConfig} */
const nextConfig = {
  // Pins the workspace root explicitly: an unrelated package-lock.json in the
  // parent home directory otherwise makes Turbopack's auto-detection infer
  // the wrong project root, which breaks build-time page collection.
  turbopack: {
    root: __dirname,
  },
};

module.exports = nextConfig;
