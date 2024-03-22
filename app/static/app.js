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
              response.data.status === "Already logged in"
            ) {
              this.isLoggedIn = true;
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
            console.log(error);
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
        })
        .catch((error) => {
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
          // Handle errors
        });
    },
    copyToClipboard(shortcut) {
      navigator.clipboard
        .writeText(shortcut)
        .then(() => {
          console.log("Shortened URL copied to clipboard");
        })
        .catch((err) => {
          console.error("Failed to copy to clipboard", err);
        });
    },
    // TODO: other methods for getting links, logging out, etc.
  },
  // On created, check if user is already logged in
  created() {
    // Attempt to get the user's links if a session already exists
  },
});
