
document.addEventListener('DOMContentLoaded', function () {
    // Dynamic event delegation for delete buttons
    document.body.addEventListener('click', function (event) {
        if (event.target.matches('.delete-user') || event.target.closest('.delete-user')) {
            event.preventDefault();
            const userId = event.target.dataset.userId || event.target.closest('.delete-user').dataset.userId;
            delete_user(event, userId);
        }
    });
});


function toggleSubmenu(event, submenuId) {
    event.preventDefault();
    const submenu = document.getElementById(submenuId);

    // Toggle visibility
    if (submenu.style.display === 'block') {
        submenu.style.display = 'none';
    } else {
        submenu.style.display = 'block';
    }
}


function deleteService(serviceId) {
    console.log(`Attempting to delete service with ID: ${serviceId}`);

    if (!confirm('Are you sure you want to delete this service?')) {
        console.log('Deletion canceled by the user.');
        return;
    }

    fetch(`/admin/services/delete/${serviceId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        console.log(`Received response: ${response.status}`);
        if (!response.ok) {
            return response.json().then(data => {
                console.error('Error from backend:', data.error);
                throw new Error(data.error || 'Failed to delete service.');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Backend response:', data);
        if (data.message) {
            alert(data.message);

            const row = document.querySelector(`tr[data-id="${serviceId}"]`);
            if (row) {
                console.log('Removing row from the table.');
                row.remove();
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    });
}




// JavaScript for Assign Employees
function assignEmployees(serviceId) {
    const employeeIds = prompt("Įveskite kableliais atskirtus darbuotojų ID:");
    if (!employeeIds) return;

    fetch('/admin/services/assign-employees', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ service_id: serviceId, employee_ids: employeeIds.split(',') })
    })
    .then(response => response.json())
    .then(data => alert(data.message || 'Darbuotojai sėkmingai paskirti!'))
    .catch(error => console.error('Error:', error));
}

//edit service
function openEditModal(serviceId) {
    if (!serviceId) {
        alert('Service ID is not provided!');
        return;
    }

    const row = document.querySelector(`tr[data-id="${serviceId}"]`);
    if (!row) {
        alert('Service not found in the table.');
        return;
    }

    // Populate form fields based on table data
    const name = row.querySelector('td:nth-child(1)').innerText.trim();
    const description = row.querySelector('td:nth-child(2)').innerText.trim();
    const price = row.querySelector('td:nth-child(3)').innerText.trim();
    const duration = row.querySelector('td:nth-child(4)').innerText.trim();
    const currentCategory = row.querySelector('td:nth-child(5)').innerText.trim();

    document.getElementById('editServiceName').value = name;
    document.getElementById('editDescription').value = description;
    document.getElementById('editPrice').value = price;
    document.getElementById('editDuration').value = duration;

    // Fetch and populate category dropdown
    const categoryDropdown = document.getElementById('edit-category-dropdown');
    fetch('/admin/services/categories')
        .then(response => response.json())
        .then(categories => {
            categoryDropdown.innerHTML = ''; // Clear existing options
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                if (category.name === currentCategory) {
                    option.selected = true;
                }
                categoryDropdown.appendChild(option);
            });
        })
        .catch(error => console.error('Error fetching categories:', error));

    // Attach serviceId to the form for submission
    document.getElementById('editServiceForm').dataset.serviceId = serviceId;

    // Open the modal
    $('#editServiceModal').modal('show');
}












// Edit category functionality
        window.editCategory = function (categoryId) {
            const newName = prompt("Enter a new name for the category:");
            if (!newName) return;

            fetch(`/admin/services/edit-category`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category_id: categoryId, name: newName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Category updated successfully!');
                    location.reload();
                } else {
                    alert('Error updating category: ' + data.error);
                }
            })
            .catch(error => console.error('Error:', error));
        };


// Delete category functionality
window.deleteCategory = function (categoryId) {
    if (!confirm("Are you sure you want to delete this category?")) return;

    fetch(`/admin/services/delete-category/${categoryId}`, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Category deleted successfully!');

            // Remove the row from the table without reloading the page
            const row = document.querySelector(`tr[data-id="${categoryId}"]`);
            if (row) row.remove();
        } else {
            alert('Error deleting category: ' + data.error);
        }
    })
    .catch(error => console.error('Error:', error));
};

function delete_user(event, userId) {
    event.preventDefault();

    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }

    fetch(`/admin/naudotojai/delete-user/${userId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to delete user.');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.message) {
            alert(data.message);

            // Remove the row from the table without reloading
            const row = document.querySelector(`tr[data-id="${userId}"]`);
            if (row) row.remove();
        }
    })
    .catch(error => {
        alert(`Error: ${error.message}`);
        console.error('Error:', error);
    });
}






function enableEdit(event, userId) {
    event.preventDefault();

    // Get the row for the user
    const row = document.querySelector(`tr[data-id="${userId}"]`);

    // Get current values
    const email = row.querySelector('.email').innerText;
    const firstName = row.querySelector('.first_name').innerText;
    const lastName = row.querySelector('.last_name').innerText;
    const role = row.querySelector('.role').innerText;

    // Replace the cells with input fields
    row.innerHTML = `
        <td><input type="text" class="form-control" id="edit-email-${userId}" value="${email}"></td>
        <td><input type="text" class="form-control" id="edit-first-name-${userId}" value="${firstName}"></td>
        <td><input type="text" class="form-control" id="edit-last-name-${userId}" value="${lastName}"></td>
        <td><input type="text" class="form-control" id="edit-role-${userId}" value="${role}"></td>
        <td>
            <button class="btn btn-success" onclick="saveEdit(event, ${userId})">Save</button>
            <button class="btn btn-secondary" onclick="cancelEdit(event, ${userId}, '${email}', '${firstName}', '${role}')">Cancel</button>
        </td>
    `;
}

function saveEdit(event, userId) {
    event.preventDefault();

    // Get updated values
    const email = document.getElementById(`edit-email-${userId}`).value;
    const firstName = document.getElementById(`edit-first-name-${userId}`).value;
    const lastName = document.getElementById(`edit-last-name-${userId}`).value;
    const role = document.getElementById(`edit-role-${userId}`).value;

    // Prepare data to send to the server
    const data = {
        user_id: userId,
        email: email,
        first_name: firstName,
        last_name: lastName,
        role: role,
    };

    // Send the update request to the server
    fetch(`/admin/naudotojai/update-user`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to update user');
        return response.json();
    })
    .then(() => {
        // Replace input fields with the updated data
        const row = document.querySelector(`tr[data-id="${userId}"]`);
        row.innerHTML = `
            <td class="email">${email}</td>
            <td class="first_name">${firstName}</td>
            <td class="last_name">${lastName}</td>
            <td class="role">${role}</td>
            <td>
                <a href="#" class="text-primary" title="View">
                    <i class="fa fa-eye"></i>
                </a>
                <a href="#" class="text-info mx-2 edit-btn" title="Edit" onclick="enableEdit(event, ${userId})">
                    <i class="fa fa-pencil-alt"></i>
                </a>
                <a href="#" class="text-danger" onclick="delete_user(event, ${userId})" title="Delete">
                    <i class="fa fa-trash"></i>
                </a>
            </td>
        `;
        alert('User updated successfully');
    })
    .catch(error => {
        console.error('Error updating user:', error);
        alert('Error updating user');
    });
}

function cancelEdit(event, userId, email, firstName, lastName, role) {
    event.preventDefault();

    // Revert back to the original row content
    const row = document.querySelector(`tr[data-id="${userId}"]`);
    row.innerHTML = `
        <td class="email">${email}</td>
        <td class="first_name">${firstName}</td>
        <td class="last_name">${lastName}</td>
        <td class="role">${role}</td>
        <td>
            <a href="#" class="text-primary" title="View">
                <i class="fa fa-eye"></i>
            </a>
            <a href="#" class="text-info mx-2 edit-btn" title="Edit" onclick="enableEdit(event, ${userId})">
                <i class="fa fa-pencil-alt"></i>
            </a>
            <a href="#" class="text-danger" onclick="delete_user(event, ${userId})" title="Delete">
                <i class="fa fa-trash"></i>
            </a>
        </td>
    `;
}

function viewUserDetails(event, userId) {
    event.preventDefault();

    // Fetch user details from the server
    fetch(`/admin/naudotojai/user-details/${userId}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch user details');
            return response.json();
        })
        .then(user => {
            // Populate the modal with user details
            document.getElementById('user-id').textContent = user.id;
            document.getElementById('user-email').textContent = user.email;
            document.getElementById('user-first-name').textContent = user.first_name;
            document.getElementById('user-last-name').textContent = user.last_name;
            document.getElementById('user-role').textContent = user.role;

            // Show the modal
            $('#viewUserModal').modal('show');
        })
        .catch(error => {
            console.error('Error fetching user details:', error);
            alert('Error loading user details');
        });
}

// APSILANKYMAI_ADMIN.html
function viewUzsakymas(event, uzsakymasId) {
    event.preventDefault();

    fetch(`/uzsakymai/details/${uzsakymasId}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch order details');
            return response.json();
        })
        .then(data => {
            // Populate modal fields
            document.getElementById('view-email').textContent = data.email;
            document.getElementById('view-tel-nr').textContent = data.tel_nr;
            document.getElementById('view-service-id').textContent = data.service_name;
            document.getElementById('view-date').textContent = data.date;
            document.getElementById('view-time').textContent = data.time;
            document.getElementById('view-employee').textContent = data.employee;
            document.getElementById('view-uzsakovas').textContent = data.uzsakovas;
            document.getElementById('view-status').textContent = data.status;
            document.getElementById('view-species').textContent = data.species || 'N/A';
            document.getElementById('view-animal-name').textContent = data.animal_name || 'N/A';
            document.getElementById('view-symptoms').textContent = data.symptoms || 'N/A';
            document.getElementById('view-gydymas').textContent = data.treatment || 'N/A';

            // Show modal
            $('#viewUzsakymasModal').modal('show');
        })
        .catch(error => {
            console.error('Error fetching order details:', error);
            alert('Error loading order details.');
        });
}


function enableEditApsilankymai(event, uzsakymasId) {
    event.preventDefault();

    const row = document.querySelector(`tr[data-id="${uzsakymasId}"]`);

    // Get current values from the row
    const email = row.querySelector('.email')?.innerText || '';
    const telNr = row.querySelector('.tel_nr')?.innerText || '';
    const firstName = row.querySelector('.first_name')?.innerText || '';
    const lastName = row.querySelector('.last_name')?.innerText || '';
    const serviceId = row.querySelector('.service_id')?.innerText || '';
    const date = row.querySelector('.date')?.innerText || '';
    const time = row.querySelector('.time')?.innerText || '';
    const employee = row.querySelector('.employee')?.innerText || '';
    const status = row.querySelector('.status')?.innerText || '';

    // Replace table cells with input fields
    row.innerHTML = `
        <td><input type="text" class="form-control" value="${email}" id="edit-email-${uzsakymasId}"></td>
        <td><input type="text" class="form-control" value="${telNr}" id="edit-tel-${uzsakymasId}"></td>
        <td><input type="text" class="form-control" value="${firstName}" id="edit-first-name-${uzsakymasId}"></td>
        <td><input type="text" class="form-control" value="${lastName}" id="edit-last-name-${uzsakymasId}"></td>
        <td><input type="text" class="form-control" value="${serviceId}" id="edit-service-id-${uzsakymasId}"></td>
        <td><input type="date" class="form-control" value="${date}" id="edit-date-${uzsakymasId}"></td>
        <td><input type="time" class="form-control" value="${time}" id="edit-time-${uzsakymasId}"></td>
        <td><input type="text" class="form-control" value="${employee}" id="edit-employee-${uzsakymasId}" readonly></td>
        <td>
            <select id="edit-status-${uzsakymasId}" class="form-control">
                <option value="Vykdoma" ${status === 'Vykdoma' ? 'selected' : ''}>Vykdoma</option>
                <option value="Atlikta" ${status === 'Atlikta' ? 'selected' : ''}>Atlikta</option>
                <option value="Atšaukta" ${status === 'Atšaukta' ? 'selected' : ''}>Atšaukta</option>
            </select>
        </td>
        <td>
            <button class="btn btn-success" onclick="saveEditApsilankymai(event, ${uzsakymasId})">Save</button>
            <button class="btn btn-secondary" onclick="cancelEditApsilankymai(event, ${uzsakymasId},
                '${encodeURIComponent(email)}',
                '${encodeURIComponent(telNr)}',
                '${encodeURIComponent(firstName)}',
                '${encodeURIComponent(lastName)}',
                '${encodeURIComponent(serviceId)}',
                '${encodeURIComponent(date)}',
                '${encodeURIComponent(time)}',
                '${encodeURIComponent(employee)}',
                '${encodeURIComponent(status)}')">Cancel</button>
        </td>
    `;
}




function saveEditApsilankymai(event, uzsakymasId) {
    event.preventDefault();

    // Safely get updated values from input fields
    const email = document.getElementById(`edit-email-${uzsakymasId}`)?.value || '';
    const telNr = document.getElementById(`edit-tel-${uzsakymasId}`)?.value || '';
    const firstName = document.getElementById(`edit-first-name-${uzsakymasId}`)?.value || '';
    const lastName = document.getElementById(`edit-last-name-${uzsakymasId}`)?.value || '';
    const serviceId = document.getElementById(`edit-service-id-${uzsakymasId}`)?.value || '';
    const date = document.getElementById(`edit-date-${uzsakymasId}`)?.value || '';
    const time = document.getElementById(`edit-time-${uzsakymasId}`)?.value || '';
    const employee = document.getElementById(`edit-employee-${uzsakymasId}`)?.value || '';
    const statusDropdown = document.getElementById(`edit-status-${uzsakymasId}`);
    const status = statusDropdown ? statusDropdown.value : '';

    const data = {
        uzsakymas_id: uzsakymasId,
        email,
        tel_nr: telNr,
        first_name: firstName,
        last_name: lastName,
        service_id: serviceId, // Submit service ID
        date,
        time,
        status,
    };

    // Send data to the backend
    fetch('/uzsakymai/update-uzsakymas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
        .then(response => {
            if (!response.ok) throw new Error('Failed to save changes');
            return response.json();
        })
        .then(() => {
            // Replace input fields with updated static text
            const row = document.querySelector(`tr[data-id="${uzsakymasId}"]`);
            row.innerHTML = `
                <td class="email">${email}</td>
                <td class="tel_nr">${telNr}</td>
                <td class="first_name">${firstName}</td>
                <td class="last_name">${lastName}</td>
                <td class="service_id">${serviceId}</td>
                <td class="date">${date}</td>
                <td class="time">${time}</td>
                <td class="employee">${employee}</td>
                <td class="status">${status}</td>
                <td>
                    <a href="#" class="text-primary mx-2" title="View" onclick="viewUzsakymas(event, ${uzsakymasId})">
                        <i class="fa fa-eye"></i>
                    </a>
                    <a href="#" class="text-info mx-2" title="Edit" onclick="enableEditApsilankymai(event, ${uzsakymasId})">
                        <i class="fa fa-pencil-alt"></i>
                    </a>
                    <a href="#" class="text-danger mx-2" title="Delete" onclick="deleteUzsakymas(${uzsakymasId})">
                        <i class="fa fa-trash"></i>
                    </a>
                </td>
            `;
            alert('Order updated successfully!');
        })
        .catch(error => {
            console.error('Error saving changes:', error);
            alert('Failed to save changes.');
        });
}





function cancelEditApsilankymai(event, uzsakymasId, email, telNr, firstName, lastName, serviceId, date, time, employee, status) {
    event.preventDefault();

    const row = document.querySelector(`tr[data-id="${uzsakymasId}"]`);

    // Decode values to handle special characters
    const decodedEmail = decodeURIComponent(email);
    const decodedTelNr = decodeURIComponent(telNr);
    const decodedFirstName = decodeURIComponent(firstName);
    const decodedLastName = decodeURIComponent(lastName);
    const decodedServiceId = decodeURIComponent(serviceId);
    const decodedDate = decodeURIComponent(date);
    const decodedTime = decodeURIComponent(time);
    const decodedEmployee = decodeURIComponent(employee);
    const decodedStatus = decodeURIComponent(status);

    // Reconstruct the original row with plain text for status
    row.innerHTML = `
        <td class="email">${decodedEmail}</td>
        <td class="tel_nr">${decodedTelNr}</td>
        <td class="first_name">${decodedFirstName}</td>
        <td class="last_name">${decodedLastName}</td>
        <td class="service_id">${decodedServiceId}</td>
        <td class="date">${decodedDate}</td>
        <td class="time">${decodedTime}</td>
        <td class="employee">${decodedEmployee}</td>
        <td class="status">${decodedStatus}</td>
        <td>
            <a href="#" class="text-primary mx-2" title="View" onclick="viewUzsakymas(event, ${uzsakymasId})">
                <i class="fa fa-eye"></i>
            </a>
            <a href="#" class="text-info mx-2" title="Edit" onclick="enableEditApsilankymai(event, ${uzsakymasId})">
                <i class="fa fa-pencil-alt"></i>
            </a>
            <a href="#" class="text-danger mx-2" title="Delete" onclick="deleteUzsakymas(${uzsakymasId})">
                <i class="fa fa-trash"></i>
            </a>
        </td>
    `;
}


function deleteUzsakymas(uzsakymasId) {
    if (!confirm('Are you sure you want to delete this order?')) {
        return;
    }

    fetch(`/uzsakymai/delete/${uzsakymasId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ uzsakymasId }),
    })
        .then(response => {
            if (response.ok) {
                // Remove the deleted row
                const row = document.querySelector(`tr[data-id="${uzsakymasId}"]`);
                if (row) row.remove();
                alert('Order deleted successfully!');
            } else {
                alert('Failed to delete order.');
            }
        })
        .catch(error => {
            console.error('Error deleting order:', error);
            alert('An error occurred while deleting the order.');
        });
}


// loading services


//loading employees
