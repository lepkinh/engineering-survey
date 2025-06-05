    // main.js

// Handle survey form submission
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("surveyForm");
    if (form) {
        form.onsubmit = async function(e) {
            e.preventDefault();
            const name = document.getElementById("name").value.trim();
            const gpa = parseFloat(document.getElementById("gpa").value);
            const firstChoice = document.getElementById("firstChoice").checked;
            const major = document.getElementById("major").value;
            const program = document.getElementById("program").value;
            const gender = document.getElementById("gender").value;
            const msg = document.getElementById("msg");

            // validation
            if (!name || name.length < 2 || name.length > 40) {
                msg.innerText = "Please enter a valid name or alias.";
                return;
            }
            if (isNaN(gpa) || gpa < 4.0 || gpa > 12.0) {
                msg.innerText = "GPA must be between 4.0 and 12.0.";
                return;
            }
            if (!major || !program || !gender) {
                msg.innerText = "Please select all options.";
                return;
            }

            try {
                const res = await fetch('https://engineering-survey.onrender.com/submit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name, gpa, first_choice: firstChoice, major, program, gender })
                });
                if (res.ok) {
                    msg.innerText = "Submitted! Thank you!";
                    form.reset();
                } else {
                    msg.innerText = "Failed to submit. Please try again.";
                }
            } catch (err) {
                msg.innerText = "Network error, please try again.";
            }
        };
    }

    // Data visualization (for data.html)
    if (window.location.pathname.endsWith('data.html')) {
        // Fetch and render data every 20 seconds
        async function fetchDataAndRender() {
            try {
                const res = await fetch('https://engineering-survey.onrender.com/data');
                const data = await res.json();

                // 1. Show cutoff
                document.getElementById('cutoff').innerHTML = data.cutoff ?
                `<h2>The cutoff for computer engineering was <b>${data.cutoff.toFixed(2)}</b></h2>`
                : "<h2>No data for cutoff yet.</h2>";

                // 2. Pie chart
                const ctxPie = document.getElementById('pieChart').getContext('2d');
                if (window.pieChart) window.pieChart.destroy();
                window.pieChart = new Chart(ctxPie, {
                    type: 'pie',
                    data: {
                        labels: [
                            "No Free Choice",
                            "Free Choice (Above Cutoff)",
                            "Free Choice (Below Cutoff)"
                        ],
                        datasets: [{
                            data: [
                                data.pie.no_free_choice,
                                data.pie.fc_above_cutoff,
                                data.pie.fc_below_cutoff
                            ]
                        }]
                    }
                });

                // 3. GPA Histogram
                const ctxGpa = document.getElementById('gpaChart').getContext('2d');
                if (window.gpaChart) window.gpaChart.destroy();
                window.gpaChart = new Chart(ctxGpa, {
                    type: 'bar',
                    data: {
                        labels: data.gpa_bins,
                        datasets: [{
                            label: "Computer Eng. GPA Distribution",
                            data: data.gpa_counts
                        }]
                    }
                });

                // 4. Gender Pie
                const ctxGender = document.getElementById('genderChart').getContext('2d');
                if (window.genderChart) window.genderChart.destroy();
                window.genderChart = new Chart(ctxGender, {
                    type: 'pie',
                    data: {
                        labels: ['Male', 'Female', 'Other'],
                        datasets: [{
                            data: [
                                data.gender_counts.male,
                                data.gender_counts.female,
                                data.gender_counts.other
                            ]
                        }]
                    },
                    options: { plugins: { title: { display: true, text: 'Gender Breakdown (Computer Eng.)' } } }
                });

            } catch (e) {
                document.getElementById('cutoff').innerHTML = "Error loading data.";
            }
        }
        fetchDataAndRender();
        setInterval(fetchDataAndRender, 20000);
    }
});
