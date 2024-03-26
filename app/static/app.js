new Vue({
  el: "#app",
  data: {
    serviceURL: "https://cs3103.cs.unb.ca:8042",
    username: "",
    password: "",
    isLoggedIn: false,
    newLink: "",
    links: [],
  },
  methods: {
    login() {
      if (this.username !== "" && this.password !== "") {
        axios
          .post(
            this.serviceURL + "/login",
            {
              username: this.username,
              password: this.password,
            },
            { withCredentials: true }
          )
          .then(() => {
            this.isLoggedIn = true;
            localStorage.setItem("isLoggedIn", this.isLoggedIn);
            this.fetchLinks();
            this.username = "";
          })
          .catch((error) => {
            alert("Error during login. Please try again.");
            console.log("Logout failed:", error);
          })
          .finally(() => {
            this.password = "";
          });
      } else {
        alert("Both username and password fields are required.");
      }
    },
    logout() {
      axios
        .delete(this.serviceURL + "/logout", { withCredentials: true })
        .then(() => {
          this.isLoggedIn = false;
          localStorage.setItem("isLoggedIn", this.isLoggedIn);
          this.links = [];
        })
        .catch((error) => {
          alert("Logout failed. Please try again.");
          console.error("Logout failed:", error);
        });
    },
    createLink() {
      axios
        .post(
          this.serviceURL + "/links",
          {
            destination: this.newLink.trim(),
          },
          { withCredentials: true }
        )
        .then((response) => {
          this.links.push(response.data);
          this.copyToClipboard(this.serviceURL + "/" + response.data.shortcut);
        })
        .catch((error) => {
          alert("Creating shortcut failed. Please try again.");
          console.error("Creating shortcut failed:", error);
        })
        .finally(() => {
          this.newLink = "";
        });
    },
    copyToClipboard(shortcut) {
      navigator.clipboard
        .writeText(shortcut)
        .then(() => {
          alert("Shortcut copied to clipboard: " + shortcut);
          console.log("Shortcut copied to clipboard");
        })
        .catch((error) => {
          alert("Failed to copy to clipboard. Please try again.");
          console.error("Failed to copy to clipboard", error);
        });
    },
    fetchLinks() {
      axios
        .get(this.serviceURL + "/links", { withCredentials: true })
        .then((response) => {
          this.links = response.data;
        })
        .catch((error) => {
          alert("Failed to fetch user links.");
          console.error("Failed to fetch links:", error);
        });
    },
    deleteLink(linkId) {
      axios
        .delete(this.serviceURL + "/links/" + linkId, {
          withCredentials: true,
        })
        .then(() => {
          this.links = this.links.filter((link) => link.linkId !== linkId);
        })
        .catch((error) => {
          alert(
            "Failed to copy to clipboard. Please try again or refresh the page."
          );
          console.error("Failed to delete link:", error);
        });
    },
  },
  created() {
    this.isLoggedIn = localStorage.getItem("isLoggedIn") === "true";

    axios
      .get(this.serviceURL + "/check-session", { withCredentials: true })
      .then((response) => {
        this.isLoggedIn = response.data.isLoggedIn;
        localStorage.setItem("isLoggedIn", this.isLoggedIn);

        if (this.isLoggedIn) {
          this.fetchLinks();
        }
      })
      .catch((error) => {
        console.error("Session check failed:", error);
        this.isLoggedIn = false;
        localStorage.setItem("isLoggedIn", "false");
      });
  },
});
