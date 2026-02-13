<template>
  <div class="skeleton-card">
    <div class="skeleton-thumbnail"></div>
    <div class="skeleton-title"></div>
    <div class="skeleton-cat"></div>
  </div>
</template>

<style scoped>
.skeleton-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}
.skeleton-thumbnail {
  width: 100%;
  aspect-ratio: 2 / 3;
  background: var(--surface-2, #ddd);
  border-radius: 6px;
  animation: pulse 1.5s infinite;
}
.skeleton-title {
  height: 14px;
  width: 80%;
  background: var(--surface-2, #ddd);
  border-radius: 4px;
  animation: pulse 1.5s infinite;
}
.skeleton-cat {
  height: 10px;
  width: 40%;
  background: var(--surface-2, #ddd);
  border-radius: 4px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 0.3; }
  100% { opacity: 0.6; }
}
</style>
