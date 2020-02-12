<template>
  <div id="app">
    <h1>rock-paper-scissors</h1>
    <Capture/>
  </div>
</template>

<script>
import Capture from './components/Capture.vue'

export default {
  name: 'app',
  components: {
    Capture
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
