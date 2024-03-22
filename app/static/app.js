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
          this.username = "";
          this.password = "";
          this.links = [];
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
          console.error("Creating shortcut failed:", error);
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
