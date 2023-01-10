<template>
  <div class="card mb-4">
    <div class="card-content">
      <div class="content">
        {{ note.content }}
        <div class="has-text-right has-text-grey-light mt-2">
          <small>{{ characterLength }}</small>
        </div>
      </div>
    </div>
    <footer class="card-footer">
      <a href="#" class="card-footer-item">Edit</a>
      <a
        @click.prevent="storeNotes.deleteNote(note.id)"
        class="card-footer-item"
      >
        Delete
      </a>
    </footer>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useStoreNotes } from "@/stores/storeNotes.js";

/*
  stores
*/

const storeNotes = useStoreNotes();

/*
  props
*/

const props = defineProps({
  note: {
    type: Object,
    required: true,
  },
});

/*
  computed
*/
const characterLength = computed(() => {
  let len = props.note.content.length;
  let description = len > 1 ? "characters" : "character";
  return `${len} ${description}`;
});
</script>
