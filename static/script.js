/* ================================
   PASSWORD VISIBILITY
================================ */

function togglePassword() {

    const passwordInput = document.getElementById("password");
    const button = document.querySelector(".toggle-password");

    if (!passwordInput) {
        return;
    }

    if (passwordInput.type === "password") {

        passwordInput.type = "text";
        button.textContent = "Hide";

    } else {

        passwordInput.type = "password";
        button.textContent = "Show";
    }
}


/* ================================
   ADD ACCOUNT MODAL
================================ */

function openAddModal() {

    const modal = document.getElementById("addModal");

    if (modal) {
        modal.classList.add("active");
    }
}


function closeAddModal() {

    const modal = document.getElementById("addModal");

    if (modal) {
        modal.classList.remove("active");
    }
}


/* ================================
   EDIT ACCOUNT MODAL
================================ */

function openEditModal(holder, pin, balance) {

    const modal = document.getElementById("editModal");

    const holderInput = document.getElementById("editHolder");
    const pinInput = document.getElementById("editPin");
    const balanceInput = document.getElementById("editBalance");

    if (!modal) {
        return;
    }

    holderInput.value = holder;
    pinInput.value = pin;
    balanceInput.value = balance;

    modal.classList.add("active");
}


function closeEditModal() {

    const modal = document.getElementById("editModal");

    if (modal) {
        modal.classList.remove("active");
    }
}


/* ================================
   DELETE MODAL
================================ */

function confirmDelete(holder) {

    const modal = document.getElementById("deleteModal");

    const holderText = document.getElementById("deleteHolder");

    const deleteLink = document.getElementById("deleteLink");

    if (!modal) {
        return;
    }

    holderText.textContent = holder;

    deleteLink.href =
        "/delete/" + encodeURIComponent(holder);

    modal.classList.add("active");
}


function closeDeleteModal() {

    const modal = document.getElementById("deleteModal");

    if (modal) {
        modal.classList.remove("active");
    }
}


/* ================================
   SEARCH ACCOUNTS
================================ */

function searchAccounts() {

    const input =
        document.getElementById("searchInput");

    const table =
        document.getElementById("accountsTable");

    if (!input || !table) {
        return;
    }

    const searchValue =
        input.value.toLowerCase().trim();

    const rows =
        table.querySelectorAll("tbody tr");

    rows.forEach(function(row) {

        const text =
            row.textContent.toLowerCase();

        if (text.includes(searchValue)) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }

    });
}


/* ================================
   CLOSE MODALS WHEN CLICKING OUTSIDE
================================ */

window.addEventListener("click", function(event) {

    const addModal =
        document.getElementById("addModal");

    const editModal =
        document.getElementById("editModal");

    const deleteModal =
        document.getElementById("deleteModal");


    if (event.target === addModal) {
        closeAddModal();
    }

    if (event.target === editModal) {
        closeEditModal();
    }

    if (event.target === deleteModal) {
        closeDeleteModal();
    }

});


/* ================================
   ESC KEY CLOSES MODALS
================================ */

document.addEventListener("keydown", function(event) {

    if (event.key !== "Escape") {
        return;
    }

    closeAddModal();
    closeEditModal();
    closeDeleteModal();

});
