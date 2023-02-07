<template>
  <div class="box">
    <h1 class="title">Generate Statistics of Discrete Global Grid Systems</h1>
  </div>

  <div class="columns">
    <div class="column is-3">
      <div class="field">
        <label class="label">Select DGGS Type:</label>
        <div class="control select is-primary">
          <select v-model="dggs_sel">
            <option v-for="f in dggs_types.types" :key="f" :value="f">{{ f }}</option>
          </select>
        </div>
      </div>
      <!--
      <div class="field">
        <label class="label">Select output format:</label>
        <div class="control select is-primary">
          <select v-model="sel_format">
            <option v-for="f in outformat_default.formats" :key="f" :value="f">{{ f }}</option>
          </select>
        </div>
      </div>
      -->
      <div class="field">
        <div class="control">
          <button id="stats_button" class="button is-link" @click="getCSV">Stats CSV</button>
        </div>
      </div>
      <!--
      <div class="field">
        <div class="control">
          <button id="gridgen_button" class="button is-info">Download CSV</button>
        </div>
      </div>
      -->
      <div>dggs: {{ dggs_sel }} output to {{ sel_format }}
        <p v-if="loading">
          Loading...
        </p>
        <p v-if="error">
          {{ error_info }}
        </p>
      </div>
    </div>

    <div class="column is-9 is-offset-3" v-if="table_data.data">
      <tt>{{ table_data.data[dggs_sel] }}</tt>
      <table class="table">
        <thead>
          <tr>
            <th v-for="el in table_data.data[dggs_sel]" :key="el" :value="el">{{ el }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="el in table_data.data[dggs_sel]" :key="k" :value="v">{{ v }}
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div class="columns pt-2">
    <div class="column">

      <Footer />

    </div>
  </div>

</template>

<script setup>
import Footer from '@/components/Footer.vue';
import { ref, onMounted } from 'vue';
import { reactive, computed } from 'vue'

const outformat_default = ref({ formats: ["TABLE", "CSV"] });
const sel_format = ref("TABLE");

const dggs_types = ref({
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
});

const dggs_sel = ref("ISEA3H");

const table_data = reactive({ data: null });
const loading = ref(false);
const error = ref(null);
const error_info = ref(null);

const getData = () => {
  error.value = false
  loading.value = true;
  const data_url = `https://dggrid-py-bozea3cspa-ew.a.run.app/api/grid_stats/${dggs_sel.value}?format=${sel_format.value}`;

  fetch(data_url)
    .then(response => response.json()).then(data => {
      table_data.data = data;
      console.log(table_data.data);

      loading.value = false;
    }).catch((error_obj) => {
      error.value = true;
      console.log(error_obj);
      error_info.value = 'Looks like there was a problem: \n' + error_obj;
      loading.value = false;
    });
}

const getCSV = () => {
  error.value = false
  loading.value = true;
  const data_url = `https://dggrid-py-bozea3cspa-ew.a.run.app/api/grid_stats/${dggs_sel.value}?format=CSV`;

  fetch(data_url)
    .then(response => response.blob()).then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      // the filename you want
      a.download = `${dggs_sel.value}.csv`;
      document.body.appendChild(a);
      a.click();
      // a.remove();

      loading.value = false;
    }).catch((error_obj) => {
      error.value = true;
      console.log(error_obj);
      error_info.value = 'Looks like there was a problem: \n' + error_obj;
      loading.value = false;
    });
}
</script>

