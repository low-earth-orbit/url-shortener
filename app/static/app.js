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
          .then((response) => {
            if (
              response.data.status === "OK" ||
              response.data.status === "Created" ||
              response.data.status === "Already logged in"
            ) {
              this.isLoggedIn = true;
              this.fetchLinks();
            } else {
              alert(
                "The username or password was incorrect. Please try again."
              );
            }
            this.username = "";
            this.password = "";
          })
          .catch((error) => {
            alert("Error during login. Please try again.");
            console.log("Logout failed:", error);
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
          "https://cs3103.cs.unb.ca:8042/user/links",
          {
            destination: this.newLink,
          },
          { withCredentials: true }
        )
        .then((response) => {
          this.links.push(response.data);
          this.newLink = "";
        })
        .catch((error) => {
          alert("Creating shortcut failed. Please try again.");
          console.error("Creating shortcut failed:", error);
        });
    },
    copyToClipboard(shortcut) {
      navigator.clipboard
        .writeText(shortcut)
        .then(() => {
          alert("Shortcut copied to clipboard:", shortcut);
          console.log("Shortcut copied to clipboard");
        })
        .catch((error) => {
          alert("Failed to copy to clipboard. Please try again.");
          console.error("Failed to copy to clipboard", error);
        });
    },
    fetchLinks() {
      axios
        .get(this.serviceURL + "/user/links", { withCredentials: true })
        .then((response) => {
          this.links = response.data;
        })
        .catch((error) => {
          console.error("Failed to fetch links:", error);
        });
    },
    deleteLink(linkId) {
      axios
        .delete(this.serviceURL + "/user/links/" + linkId, {
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
    axios
      .get(this.serviceURL + "/check-session", { withCredentials: true })
      .then((response) => {
        this.isLoggedIn = response.data.isLoggedIn;
        if (this.isLoggedIn) {
          this.fetchLinks();
        }
      })
      .catch((error) => {
        this.isLoggedIn = false;
        console.error("Session check failed:", error);
      });
  },
});
