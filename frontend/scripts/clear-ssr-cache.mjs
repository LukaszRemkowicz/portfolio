const DEFAULT_TAGS = [
  'profile',
  'background',
  'travel-highlights',
  'latest-astro-images',
  'settings',
];

function parseArgs(argv) {
  const args = argv.slice(2);
  const allTags = args.includes('--all-tags');
  const tags = args.filter(arg => !arg.startsWith('--'));

  return {
    allTags,
    tags: allTags ? [] : tags.length > 0 ? tags : DEFAULT_TAGS,
  };
}

async function main() {
  const token = process.env.SSR_CACHE_INVALIDATION_TOKEN;
  if (!token) {
    console.error('SSR_CACHE_INVALIDATION_TOKEN is required');
    process.exit(1);
  }

  const port = process.env.PORT || process.env.FRONTEND_PORT || '8080';
  const invalidateUrl =
    process.env.SSR_CACHE_INVALIDATION_URL ||
    `http://127.0.0.1:${port}/internal/cache/invalidate`;

  const { tags } = parseArgs(process.argv);
  const response = await fetch(invalidateUrl, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ tags }),
  });

  const text = await response.text();

  if (!response.ok) {
    console.error(
      `SSR cache invalidation failed (${response.status} ${response.statusText})`
    );
    if (text) {
      console.error(text);
    }
    process.exit(1);
  }

  if (text) {
    console.log(text);
    return;
  }

  console.log(
    JSON.stringify({
      ok: true,
      tags,
    })
  );
}

main().catch(error => {
  console.error('SSR cache invalidation failed');
  console.error(error);
  process.exit(1);
});
