new Vue({
  el: "#app",
  data: {
    serviceURL: "https://cs3103.cs.unb.ca:8042",
    username: "",
    password: "",
    isLoggedIn: false,
    newLink: "",
    links: [],
    alert: {
      show: false,
      message: "",
      type: "danger",
    },
  },
  methods: {
    login() {
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
          $("#loginModal").modal("hide");
          this.fetchLinks();
          // Reset alert
          this.alert.show = false;
        })
        .catch((error) => {
          // Set alert
          this.alert.show = true;
          this.alert.message = "Error during login. Please try again.";
          this.alert.type = "danger";
          console.error("Login failed: ", error);
        })
        .finally(() => {
          this.username = "";
          this.password = "";
        });
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
          this.showToast("Logout failed. Please try again.", "error");
          console.error("Logout failed: ", error);
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
          this.showToast(
            "Creating shortcut failed. Please try again.",
            "error"
          );
          console.error("Creating shortcut failed: ", error);
        })
        .finally(() => {
          this.newLink = "";
        });
    },
    copyToClipboard(shortcut) {
      navigator.clipboard
        .writeText(shortcut)
        .then(() => {
          this.showToast("Shortcut copied to clipboard.", "success");
          console.log("Shortcut copied to clipboard: " + shortcut);
        })
        .catch((error) => {
          this.showToast(
            "Failed to copy to clipboard. Please try again.",
            "error"
          );
          console.error("Failed to copy to clipboard: ", error);
        });
    },
    fetchLinks() {
      axios
        .get(this.serviceURL + "/links", { withCredentials: true })
        .then((response) => {
          this.links = response.data;
        })
        .catch((error) => {
          this.showToast("Failed to fetch user links.", "error");
          console.error("Failed to fetch links: ", error);
        });
    },
    deleteLink(linkId) {
      axios
        .delete(this.serviceURL + "/links/" + linkId, {
          withCredentials: true,
        })
        .then(() => {
          this.links = this.links.filter((link) => link.linkId !== linkId);
          this.showToast("Shortcut deleted.", "success");
        })
        .catch((error) => {
          this.showToast(
            "Failed to delete link. Please try again or refresh the page.",
            "error"
          );
          console.error("Failed to delete link: ", error);
        });
    },
    showToast(message, type) {
      const toastContainer = document.getElementById("toastContainer");
      const toastEl = document.createElement("div");
      toastEl.classList.add(
        "toast",
        "align-items-center",
        "text-white",
        type === "error" ? "bg-danger" : "bg-success",
        "border-0"
      );
      toastEl.role = "alert";
      toastEl.ariaLive = "assertive";
      toastEl.ariaAtomic = "true";
      toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          ${message}
        </div>
        <button type="button" class="mr-2 mb-1 text-white close" data-dismiss="toast" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
    `;

      toastContainer.appendChild(toastEl);

      const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 3000,
      });
      toast.show();
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
        console.error("Session check failed: ", error);
        this.isLoggedIn = false;
        localStorage.setItem("isLoggedIn", "false");
      });
  },
});
