import { defineStore, acceptHMRUpdate } from "pinia";

export const useStoreNotes = defineStore("storeNotes", {
  // state: () => ({ notes: [] })
  state: () => {
    return {
      notes: [
        { id: "id1", content: "Lorem ipsum 1" },
        { id: "id2", content: "Lorem ipsum 2" },
        { id: "id3", content: "Lorem ipsum 3" },
      ],
    };
  },
  // getters
  // actions
  actions: {
    addNote(newNoteContent) {
      let currentDate = new Date().getTime();
      let id = currentDate.toString();
      let note = {
        id: id,
        content: newNoteContent,
      };
      this.notes.unshift(note);
    },
    deleteNote(idToDelete) {
      this.notes = this.notes.filter((note) => {
        return note.id !== idToDelete;
      });
    },
  },
});

// make sure to pass the right store definition, `useAuth` in this case.
if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useStoreNotes, import.meta.hot));
}
