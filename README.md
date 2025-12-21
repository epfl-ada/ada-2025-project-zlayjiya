# YouNiverse: Voyage Through Video Galaxies

**Team:** Adam, Yassine, Elyas, Mehdi, Mohamed



## Abstract

Throughout history, human societies have always gathered in groups bound by shared interests. With millions of users and creators interacting every day, we're convinced that YouTube is no exception. Over time, this immense digital society must have developed its own internal structure: a vast universe of connections where clusters of channels and audiences gravitate around common content. Yet for most of us, this organization remains invisible: even though we each unknowingly belong to one or many of its galaxies.

This project, **YouNiverse: Voyage through video galaxies**, aims to uncover and tell the story of YouTube's hidden architecture. Using the YouNiverse dataset, which spans **136,470 channels** and over **72 million videos** published between May 2005 and October 2019, we seek to map the platform as a digital cosmos. By building networks of co-commenting users, we aim to reveal how channels cluster into distinct "galaxies," each orbiting shared themes and cultures. Combining graph theory, NLP, and statistical analysis, we hope to reveal the unseen forces that shape how online communities form, connect, and evolve.


##  Research Questions

To explore this digital cosmos, we formulate several research questions that will guide our journey through the YouNiverse:

### 1. How do channels cluster into audience-based galaxies?

- Can we identify distinct communities through co-commenting network analysis?
- Does the ecosystem resemble a few large, dominant galaxies or a constellation of many smaller ones?
- How has the structure of this digital cosmos evolved over time: have new galaxies emerged, merged, or faded over time?


### 2. What characteristics distinguish these galaxies?

- What thematic categories dominate each galaxy?
- How are these categories defined: by single dominant themes or by mixed clusters? Do they reflect global YouTube genres or regional identities?
- How do engagement metrics vary across different communities?

### 3. How do users travel across the Youniverse?

- Do users belong to one galaxy, or do they engage across several?
- Which channels or categories serve as bridges connecting different communities?
- Can we identify echo chambers — isolated galaxies with limited cross-community interaction?

### 4. Are there dominant "black hole" channels that capture most attention?

- How unequal is attention distribution within and across galaxies?
- What distinguishes black holes across different galaxies ?


## Data Preprocessing

Given the vast size of the YouNiverse dataset, we apply the following filtering criteria to ensure computational feasibility and focus on influential channels.

### Channel Selection
We **may** filter channels according to their subscribers count, retaining only the most prominent creators. This approach focuses our analysis on channels with substantial influence while maintaining a representative sample of YouTube's content ecosystem.

### Data Integration
We link comments to videos, videos to channels, and users to their commenting activity across channels. This creates the foundation for building the co-commenting network that reveals audience overlap patterns.

### Text Preprocessing
Video titles and descriptions are lowercased, stripped of special characters, and processed to remove common stopwords, preparing the text data for natural language processing.

---

##  Methods

### Part 1: Galaxy Formation and Temporal Evolution

1. Construct co-commenting networks where nodes represent channels and edges represent shared audiences (weighted by number of common commenters).
2. **Normalize** edges based on channel size: We'll count the total amount of people that commented on the channel from the rows we've processed. 
3. Apply **Louvain community detection algorithm** to identify natural clusters (galaxies) by maximizing network modularity.
4.  Build temporal networks over time to track the evolution of the YouTube ecosystem: observing which galaxies grew, declined, merged, or emerged over ti

### Part 2: Galaxy Characterization

1. Identify dominant content themes by analyzing YouTube's official category distribution within each galaxy.
2. Apply **TF-IDF** (Term Frequency-Inverse Document Frequency) to aggregated subset of video titles from channels in each galaxy to extract distinctive keywords.
3. Compare engagement metrics (views, likes, comments, video duration) across galaxies to identify behavioral differences.
4. Derive themes through NLP Processing from keywords.

### Part 3: User Mobility and Echo Chamber Dynamics

1. Map user activity across galaxies by tracking which communities they comment in.
2. Identify galaxies with low outgoing egdes to find echo chambers. 
3. Compute **betweenness centrality** to detect "bridge channels" connecting multiple galaxies.

### Part 4: Attention Inequality and Influence Dynamics

1. Use **Gini coefficients** to quantify overall attention inequality, and concentration ratios to measure how much total attention is captured by the most dominant channels.
2. Test for power-law behavior in subscriber and view distributions to assess whether YouTube follows a "winner-takes-all" dynamic.
3. For each black-hole channel, compare the main metrics to find patterns.

---

## Proposed Timeline

### Until 5/11/2024 (Deadline Milestone P2)

**Week 1-2: Data Pipeline & Network Construction**

- **Data preprocessing:** complete data loading, integration, and channel filtering
- **Part 1: Galaxy Formation** - construct co-commenting networks, normalize edges, and apply Louvain community detection to identify initial galaxy clusters

**Deliverable:** P2 submission with feasibility demonstration including working data pipeline and initial galaxy identification.

---

### 5/11 to 30/11

**Week 3-4: Galaxy Characterization & Initial Analysis**

- **Part 2: Galaxy Characterization** - analyze category distributions, apply TF-IDF to video titles, extract themes through NLP, and compare engagement metrics across galaxies
- **Part 3: User Mobility and Echo Chamber Dynamics (Initial Phase)** - map user activity across galaxies, identify echo chambers, and begin bridge channel detection

---

### 30/11 to 8/12

**Week 5-6: Advanced Analysis & Temporal Evolution**

- **Part 3: User Mobility and Echo Chamber Dynamics (Completion)** - finalize echo chamber identification and bridge channel detection
- **Part 4: Attention Inequality and Influence Dynamics** - calculate Gini coefficients, test for power-law behavior, and analyze black-hole channel influence
- **Part 5: Temporal Evolution of the Network (Initial Implementation)** - begin building temporal networks and tracking galaxy evolution patterns

---

### 8/12 to 17/12 (Deadline Milestone P3)

**Week 7-8: Finalization & Visualization**

- **Part 5: Temporal Evolution of the Network (Completion)** - complete temporal network analysis and track galaxy evolution over time
- **Data Story Development** - design narrative structure, create interactive visualizations, and draft text synthesizing all findings
- **Repository & Documentation** - clean repository structure, finalize code documentation, and prepare final report

**Deliverable:** P3 submission with complete analysis, interactive visualizations, and comprehensive project documentation.

---

## Organization Within the Team

### Role Distribution

- **Elyas**: Network construction, community detection (Louvain), graph metrics computation, engagement metrics analysis, time series analysis, interactive dashboard development
- **Adam**: Data preprocessing, data integration, TF-IDF analysis, NLP processing and theme extraction, narrative structure design, text synthesis
- **Mohamed**: User activity mapping, echo chamber identification, bridge channel detection (betweenness centrality), user mobility analysis, interactive visualizations
- **Yassine**: Category distribution analysis, Gini coefficients, power-law testing, statistical validation, black-hole channel characteristics analysis, final report and documentation
- **Mehdi**: Edge normalization, temporal network construction, galaxy evolution tracking, black-hole channel influence analysis, repository organization and code documentation

