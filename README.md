# SASS-C Radar Data Visualization Documentation
## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [Installation](#3-installation)
4. [Usage](#4-usage)
5. [Understanding the Queries](#5-understanding-the-queries)
6. [Frequently Asked Questions (FAQs)](#6-frequently-asked-questions-faqs)
7. [Known Issues](#7-known-issues)
8. [Contributing](#8-contributing)
9. [License](#9-license)
10. [Feedback and Support](#10-feedback-and-support)

## 1. Overview

This project retrieves data from SASS-C radars, stores it in a dedicated database, and provides an intuitive visualization interface to monitor and analyze the performance of the radar. Developed using Python, it offers insights not only into real-time performance but also historical data.
## 2. Features

Data Retrieval: Seamlessly fetch data from SASS-C radars.
Database Storage: Store radar performance data efficiently in our custom database.
Data Visualization: Interactive visualizations to depict real-time and historical radar performance.
Historical Analysis: Dive deep into past data to identify patterns, anomalies, or areas of improvement.

## 3. Installation
Prerequisites

Ensure you have Python (version 3.9 or later) installed.
Other dependencies are listed in the requirements.txt.

Steps

Clone the repository:

`git clone https://github.com/dylanvkmns/RadarInsight.git`

Navigate to the project directory:

`cd RadarInsight`

Install the required packages:

`pip install -r requirements.txt`

## 4. Usage

Run migrations to set up the database:

`python manage.py migrate`

Start the server:

`python runDash.py`

Open your browser and navigate to:

`http://127.0.0.1:8050/`

This will access the visualization tool.
## 5. Understanding the Queries

The SQL queries embedded within the tool serve the purpose of extracting specific radar data elements necessary for accurate visualization. Users do not need to modify these unless they have specific additional requirements.
## 6. Frequently Asked Questions (FAQs)

Q: I'm getting a date format error. What should I do?
    A: Ensure you're inputting the date in the "dd/mm/yyyy" format, like "01/10/2023". The tool will prompt you again for the correct format if entered incorrectly.

Q: I'm facing an "Invalid value 'AUTOCOMMIT' for isolation_level" error. What should I do?
    A: Make sure you're using a compatible version of SQLAlchemy and that your database supports the AUTOCOMMIT isolation level.

## 7. Known Issues

Users might encounter issues with specific database versions, unsupported isolation levels, or particular Python versions. Always ensure you are using recommended versions and configurations.
## 8. Contributing

Contributions are always welcome! Please read our contributing guidelines to get started.
## 9. License

This project is licensed under the MIT License - see the LICENSE file for details.
## 10. Feedback and Support

For any feedback, queries, or issues related to the SASS-C Radar Data Visualization Tool, please contact the development team.

Developed with ❤️ by Dylan Veekmans.
