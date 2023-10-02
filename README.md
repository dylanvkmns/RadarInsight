# SASS-C Radar Data Visualization
## Table of contents

1.  [Overview](#overview)
2.  [Features](#features)
3.  [Installation](#installation)
4.  [Usage](#usage)
5.  [Contributing](#contributing)
6.  [License](#license)
## Overview

This project retrieves data from SASS-C radars, stores it in a dedicated database, and provides an intuitive visualization interface to monitor and analyze the performance of the radar. It offers insights not only into real-time performance but also historical data.

## Features
-   **Data Retrieval**: Seamlessly fetch data from SASS-C radars.
-   **Database Storage**: Store radar performance data efficiently in our custom database.
-   **Data Visualization**: Interactive visualizations to depict real-time and historical radar performance.
-   **Historical Analysis**: Dive deep into past data to identify patterns, anomalies, or areas of improvement.
## Installation
### Prerequisites

-   Ensure you have [Python](https://www.python.org/) (version 3.9 or later) installed.
-   Other dependencies as listed in the `requirements.txt`.
- ### Steps

1.  Clone the repository:
    

-   `git clone https://github.com/your-username/SASS-C-Radar-Tool.git` 
    
-   Navigate to the project directory:

    
-   `cd SASS-C-Radar-Tool` 
    
-   Install the required packages:

    

```bash
pip install -r requirements.txt
```
## Usage

1.  Run migrations to setup the database:

-   `python manage.py migrate` 
    
-   Start the server:

1.  `python runDahs.py` 
    
2.  Open your browser and go to `http://127.0.0.1:8050/` to access the visualization tool.

## Contributing

Contributions are always welcome! Please read our [contributing guidelines](https://chat.openai.com/c/CONTRIBUTING.md) to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

----------

Developed with ❤️ by Dylan Veekmans.
