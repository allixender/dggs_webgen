import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useDggsStore = defineStore('dggstypes', () => {
  const dggstypes = ref({
    types: ["ISEA3H",
    "ISEA4H",
    "ISEA4T",
    "ISEA4D",
    "ISEA43H",
    "ISEA7H",
    "FULLER3H",
    "FULLER4H",
    "FULLER4T",
    "FULLER4D",
    "FULLER43H",
    "FULLER7H",
    "H3",
    "RHEALPIX"]
  })
 
  return { dggstypes }
})
