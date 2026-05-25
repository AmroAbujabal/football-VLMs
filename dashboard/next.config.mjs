

const nextConfig = {
  // Allow fetching from the FastAPI backend during SSR
  async rewrites() {
    return [];
  },
};

export default nextConfig;
