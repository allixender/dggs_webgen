<template>
  <header>
    <div class="wrapper">
      <nav>
        <RouterLink class="button is-primary navhead" to="/">Home</RouterLink>
        <RouterLink class="navhead is-link button" to="/view">Explore</RouterLink>
        <RouterLink class="button is-primary navhead" to="/stats">Grid Stats</RouterLink>
        <RouterLink class="navhead is-link button" to="/generate">Generate</RouterLink>
      </nav>
    </div>
  </header>

  <RouterView />
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<style scoped>

</style>
