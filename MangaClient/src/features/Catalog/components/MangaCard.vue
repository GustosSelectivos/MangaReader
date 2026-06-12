<script setup>
import { computed } from 'vue';
import { toCdnUrl } from '@/utils/cdn';
import { typeClass, displayType, originLabel, isErotic } from '@/utils/mangaFormatters';

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    default: 0
  },
  showEroticLabel: {
    type: Boolean,
    default: false
  }
});

// Computed properties using shared formatters
const tClass = computed(() => typeClass(props.item));
const dType = computed(() => displayType(props.item));
const oLabel = computed(() => originLabel(props.item));
const isEroticItem = computed(() => isErotic(props.item));

// Link generation
const itemLink = computed(() => `/library/manga/${props.item.slug || props.item.id}`);

// Cover resolution
const coverUrl = computed(() => props.item.displayCover || props.item.cover || '');
const cdnCover = computed(() => coverUrl.value ? toCdnUrl(coverUrl.value, { w: 400, q: 80 }) : '');
</script>

<template>
  <div class="card-item">
    <a :href="itemLink" class="card-link">
      <div class="thumbnail book">
        <img 
          :src="cdnCover" 
          :alt="item.title" 
          :loading="index < 6 ? 'eager' : 'lazy'" 
          :fetchpriority="index < 4 ? 'high' : 'auto'"
          decoding="async" 
        />
        <div class="thumbnail-title top-strip">
          <h3 class="h6 m-0 text-truncate" :title="item.title">{{ item.title }}</h3>
        </div>
        
        <div class="type-bubble">
          {{ oLabel }}
          <span v-if="showEroticLabel && isEroticItem" class="age-18">+18</span>
        </div>
        
        <div class="thumbnail-type-bar" :class="tClass" :style="{ '--type-bar-color': item.dem_color || undefined }">
          {{ dType }}
        </div>
      </div>
    </a>
  </div>
</template>

<style scoped>
.card-item { list-style:none; }
.card-link { text-decoration:none; display:block; outline: none; border: none; }
.card-link:hover, .card-link:focus { outline: none; border: none; }

.thumbnail.book {
  aspect-ratio: 2 / 3;
  min-height: 220px;
  position: relative;
  border-radius: 6px;
  overflow: hidden;
  color: #fff;
  display: block;
}

.thumbnail.book img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.4s ease;
}

.thumbnail .thumbnail-title.top-strip { 
  position:absolute; top:0; left:0; right:0; background:rgba(0,0,0,0.8); padding:4px 6px; 
}
.thumbnail .thumbnail-title.top-strip h3 { 
  margin:0; font-size:14px; color:#fff; width:100%; line-height:1.15; 
}

.type-bubble { 
  position:absolute; left:8px; top:36px; background:rgba(0,0,0,0.6); color:#fff; 
  padding:3px 8px; border-radius:12px; font-size:11px; font-weight:600; 
  display:inline-flex; align-items:center; gap:6px;
}
.type-bubble .age-18 { 
  color:#ff4d4f; background:transparent; padding-left:6px; font-weight:800; 
}

.thumbnail-type-bar { 
  position:absolute; left:0; right:0; bottom:0; padding:4px 6px 5px; 
  font-size:12px; font-weight:600; letter-spacing:.3px; 
  background:linear-gradient(90deg, var(--type-bar-color, rgba(0,0,0,0.85)) 0%, rgba(0,0,0,0.6) 100%); color:#fff; 
}

.type-manga { --type-bar-color:#1e88e5; }
.type-manhwa { --type-bar-color:#43a047; }
.type-manhua { --type-bar-color:#c62828; }
.type-novela { --type-bar-color:#6a1b9a; }
.type-shounen { --type-bar-color:#1976d2; }
.type-seinen { --type-bar-color:#546e7a; }
.type-josei { --type-bar-color:#8e24aa; }
.type-shoujo { --type-bar-color:#ff4081; }
.type-default { --type-bar-color:#455a64; }

@media (max-width: 576px) {
  .thumbnail.book { aspect-ratio: 9 / 14; min-height: 170px; }
  .thumbnail-title.top-strip h3 { font-size:12px; }
  .thumbnail-type-bar { font-size:10px; padding:3px 5px 4px; }
}

@media (max-width: 420px) {
  .thumbnail.book { min-height: 160px; }
}
</style>
