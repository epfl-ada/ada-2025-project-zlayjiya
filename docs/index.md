---
layout: default
title: "YouNiverse: Voyage Through Video Galaxies"
---

<!-- Section I: Introduction -->
<section id="introduction" class="section">
    <span class="section-number">Chapter I</span>
    <h2>A Journey Through the YouNiverse</h2>
    
    <h3>Understanding the Scale of the YouNiverse</h3>
    <p>
        Over the past two decades, YouTube has evolved from a simple video-sharing website into one of the largest social ecosystems ever created. With <span class="highlight">billions of viewers and creators</span> interacting around the globe, it has become a global stage where cultures spread, trends emerge, and ideas collide.
    </p>
    <p>
        Today, YouTube is not just entertainment: it is a reflection of society, a mirror of human curiosity, and a massive accelerator of cultural exchange. From music to science, from gaming to politics, its content shapes our habits, our conversations, and often, our worldview.
    </p>
    
    <!-- Stats about YouTube -->
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">136K+</div>
            <div class="stat-label">Channels Analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">72M+</div>
            <div class="stat-label">Videos (2005-2019)</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">14</div>
            <div class="stat-label">Years of Data</div>
        </div>
    </div>
    
    <h3>Revealing a Hidden Cosmic Landscape</h3>
    <p>
        Given the sheer scale of interactions happening daily on the platform, we are convinced that YouTube cannot be understood as just a collection of videos; it behaves more like an <span class="highlight">immense digital world</span> with its own internal order.
    </p>
    <p>
        And if we zoom out—far out—this world begins to resemble a vast cosmic landscape. Individual channels appear as stars; they cluster into large thematic <span class="highlight">galaxies</span>, and within them, smaller constellations emerge around more specific interests.
    </p>
    
    <div class="quote">
        "What we experience as a chaotic stream of content may actually hide a structured universe governed by invisible forces of attraction between creators and their audiences."
    </div>
    
    <h3>A Universe We Cannot See</h3>
    <p>
        Yet, the inner order of this digital cosmos remains invisible. We travel through YouTube every day without ever seeing the structure that shapes what we discover, what we watch, and ultimately, what we think.
    </p>
    <p>
        With billions of interactions steering opinions, habits, and cultural currents, YouTube now functions as a <span class="highlight">parallel society</span>—one whose architecture remains hidden from its own inhabitants.
    </p>
    
    <h3>Our Expedition Map</h3>
    <p>To navigate this digital cosmos, our exploration is guided by four fundamental questions:</p>
    
    <div class="question-grid">
        <div class="question-card">
            <div class="question-number">01</div>
            <div class="question-title">Galaxy Formation</div>
            <div class="question-text">How do channels cluster into audience-based galaxies?</div>
        </div>
        <div class="question-card">
            <div class="question-number">02</div>
            <div class="question-title">Galaxy Identity</div>
            <div class="question-text">What thematic, structural, and temporal features distinguish these galaxies?</div>
        </div>
        <div class="question-card">
            <div class="question-number">03</div>
            <div class="question-title">User Mobility</div>
            <div class="question-text">How do viewers travel across the YouNiverse? Do they remain confined to a single constellation?</div>
        </div>
        <div class="question-card">
            <div class="question-number">04</div>
            <div class="question-title">Black Holes</div>
            <div class="question-text">Do certain channels capture disproportionate attention, shaping the dynamics of their galaxies?</div>
        </div>
    </div>
</section>

<!-- Section II: Dataset -->
<section id="dataset" class="section">
    <span class="section-number">Chapter II</span>
    <h2>Before We Explore: First Glimpses of the YouNiverse</h2>
    
    <h3>The YouNiverse Dataset</h3>
    <p>
        Our journey begins with the <span class="highlight">YouNiverse dataset</span>, a comprehensive collection spanning 136,470 channels and over 72 million videos published between May 2005 and October 2019.
    </p>
    
    <!-- TODO: Add dataset description and stats -->
    
    <h3>Power Law Distribution</h3>
    <p>
        Even before building our cosmic map, the data reveals a striking pattern: attention on YouTube follows a <span class="highlight">power law distribution</span>. A handful of channels capture most of the views, while the vast majority remain in the shadows.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">Distribution of Views and Subscribers</div>
        <div id="power-law-chart" class="viz-placeholder">
            <!-- Plotly chart will be inserted here -->
            [Interactive visualization coming soon]
        </div>
    </div>
    
    <h3>Growth Over Time</h3>
    <p>
        The YouNiverse has expanded dramatically over the years. From a small collection of channels in 2005 to a sprawling ecosystem by 2019, the platform's growth tells a story of explosive democratization of content creation.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">Growth of Videos Over Time</div>
        <div id="growth-chart" class="viz-placeholder">
            <!-- Plotly chart will be inserted here -->
            [Interactive visualization coming soon]
        </div>
    </div>
    
    <h3>Category Distribution</h3>
    <p>
        YouTube's official categories provide our first lens into the content landscape. But as we'll discover, these labels only scratch the surface of the true thematic structure.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">Distribution of Official YouTube Categories</div>
        <div id="category-chart" class="viz-placeholder">
            <!-- Plotly chart will be inserted here -->
            [Interactive visualization coming soon]
        </div>
    </div>
</section>

<!-- Section III: Galaxy Construction -->
<section id="galaxies" class="section">
    <span class="section-number">Chapter III</span>
    <h2>Constructing the Cosmic Map: From Comments to Galaxies</h2>
    
    <h3>Building the Co-Commenter Network</h3>
    <p>
        To reveal the hidden structure of YouTube, we build a network based on <span class="highlight">audience overlap</span>. The core logic: for each user, we find the Top-K channels they comment on most. We then create edges only between these Top-K channels, forming a high-signal graph of true audience affinity.
    </p>
    
    <p>
        Two channels with many shared commenters are linked by strong gravitational bonds—they orbit in the same region of the YouNiverse.
    </p>
    
    <h3>Edge Normalization</h3>
    <p>
        Raw co-commenter counts can be misleading. Two massive channels might share thousands of commenters simply due to their size. To find genuine affinity, we <span class="highlight">normalize edge weights</span> by channel size, revealing proportional audience overlap rather than absolute numbers.
    </p>
    
    <h3>Community Detection: Finding Galaxies</h3>
    <p>
        Using the <span class="highlight">Louvain algorithm</span>, we identify natural clusters—our "galaxies"—by maximizing network modularity. Each galaxy represents a group of channels bound together by shared audiences.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">The YouNiverse Network</div>
        <div id="network-viz" class="viz-placeholder">
            <!-- Network visualization will be inserted here -->
            [Interactive network visualization coming soon]
        </div>
    </div>
    
    <h3>What We Found</h3>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">XX</div>
            <div class="stat-label">Galaxies Detected</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">X.XX</div>
            <div class="stat-label">Modularity Score</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">XX%</div>
            <div class="stat-label">Channels in Top 5 Galaxies</div>
        </div>
    </div>
    
    <h3>Temporal Evolution</h3>
    <p>
        The YouNiverse is not static. Galaxies form, grow, merge, and sometimes fade over time. Our temporal analysis reveals how the cosmic landscape has evolved from 2005 to 2019.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">Evolution of the YouNiverse (2005-2019)</div>
        <div id="temporal-viz" class="viz-placeholder">
            <!-- Temporal slider visualization will be inserted here -->
            [Interactive timeline coming soon]
        </div>
    </div>
</section>

<!-- Section IV: Galaxy Identity -->
<section id="identity" class="section">
    <span class="section-number">Chapter IV</span>
    <h2>Understanding the Identity of Galaxies</h2>
    
    <h3>Thematic Characterization</h3>
    <p>
        Each galaxy has its own identity. Using <span class="highlight">topic detection</span> on video titles and descriptions, we uncover the dominant themes within each community.
    </p>
    
    <p>
        Some galaxies are dominated by a single theme (Gaming, Music), while others blend multiple categories into unique subcultures.
    </p>
    
    <h3>Single-Theme vs Multi-Theme Galaxies</h3>
    <p>
        Are galaxies defined by a single dominant category, or do they represent hybrid communities? Our analysis reveals both types exist in the YouNiverse.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">Topic Distribution Within Galaxies</div>
        <div id="topic-viz" class="viz-placeholder">
            <!-- Topic visualization will be inserted here -->
            [Interactive visualization coming soon]
        </div>
    </div>
    
    <h3>Regional vs Global Galaxies</h3>
    <p>
        Some galaxies transcend borders, uniting viewers worldwide around shared interests. Others cluster along linguistic or regional lines, forming cultural pockets within the larger universe.
    </p>
    
    <h3>Engagement Metrics by Galaxy</h3>
    <p>
        Different galaxies exhibit different engagement patterns. Gaming communities might favor longer videos, while Music galaxies see higher view counts but shorter durations.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">Engagement Metrics Comparison</div>
        <div id="engagement-viz" class="viz-placeholder">
            <!-- Engagement comparison chart will be inserted here -->
            [Interactive visualization coming soon]
        </div>
    </div>
    
    <h3>Category Evolution Over Time</h3>
    <p>
        What were the trending categories in 2010? How did major events reshape the content landscape? Our temporal category analysis reveals the shifting tides of YouTube culture.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">Rise and Fall of Content Categories</div>
        <div id="category-evolution-viz" class="viz-placeholder">
            <!-- Category evolution chart will be inserted here -->
            [Interactive visualization coming soon]
        </div>
    </div>
</section>

<!-- Section V: User Navigation -->
<section id="navigation" class="section">
    <span class="section-number">Chapter V</span>
    <h2>Navigating the YouNiverse: How Do Users Travel Between Galaxies?</h2>
    
    <h3>Mapping User Journeys</h3>
    <p>
        Do viewers stay within their home galaxy, or do they explore the broader universe? By tracking which communities users comment in, we can map the <span class="highlight">flow of attention</span> across the YouNiverse.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">User Flow Between Galaxies</div>
        <div id="flow-viz" class="viz-placeholder">
            <!-- Sankey or chord diagram will be inserted here -->
            [Interactive visualization coming soon]
        </div>
    </div>
    
    <h3>Echo Chambers: Isolated Galaxies</h3>
    <p>
        Some galaxies exhibit <span class="highlight">low outgoing edges</span>—their inhabitants rarely venture outside. These echo chambers represent communities with limited cross-pollination of ideas.
    </p>
    
    <div class="quote">
        "In a universe of infinite content, some viewers choose to orbit a single star, never exploring what lies beyond."
    </div>
    
    <h3>Bridge Channels: Cosmic Connectors</h3>
    <p>
        Using <span class="highlight">betweenness centrality</span>, we identify channels that serve as bridges between galaxies—cosmic connectors that help ideas flow across community boundaries.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">Top Bridge Channels</div>
        <div id="bridge-viz" class="viz-placeholder">
            <!-- Bridge channels visualization will be inserted here -->
            [Interactive visualization coming soon]
        </div>
    </div>
</section>

<!-- Section VI: Black Holes -->
<section id="blackholes" class="section">
    <span class="section-number">Chapter VI</span>
    <h2>The Black Holes of the YouNiverse</h2>
    <h3>When Attention Collapses Around a Few Stars</h3>
    
    <p>
        In every galaxy, a few channels exert <span class="highlight">disproportionate gravitational pull</span>. These "black holes" capture massive amounts of attention, shaping the dynamics of their entire region.
    </p>
    
    <h3>Attention Distribution</h3>
    <p>
        Using <span class="highlight">Gini coefficients</span>, we quantify the inequality of attention distribution. The results confirm what many suspect: YouTube exhibits a "winner-takes-all" dynamic.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">Attention Inequality Across Galaxies</div>
        <div id="gini-viz" class="viz-placeholder">
            <!-- Gini coefficient visualization will be inserted here -->
            [Interactive visualization coming soon]
        </div>
    </div>
    
    <h3>Identifying the Black Holes</h3>
    <p>
        Who are the black holes of each galaxy? What characteristics do they share? Our analysis reveals patterns in posting frequency, video duration, and content style.
    </p>
    
    <div class="viz-container">
        <div class="viz-title">Black Hole Channels by Galaxy</div>
        <div id="blackhole-viz" class="viz-placeholder">
            <!-- Black hole channels visualization will be inserted here -->
            [Interactive visualization coming soon]
        </div>
    </div>
    
    <h3>Influence on Surrounding Channels</h3>
    <p>
        Do black holes drive the content and dynamics of smaller channels in their orbit? Our time series analysis reveals how dominant channels influence their neighbors.
    </p>
    
    <div class="quote">
        "With great reach comes great responsibility. The black holes of YouTube don't just consume attention—they shape the very fabric of their galaxies."
    </div>
</section>

<!-- Conclusion -->
<section class="section">
    <span class="section-number">Epilogue</span>
    <h2>Charting the Future of the YouNiverse</h2>
    
    <p>
        Our voyage through the YouNiverse has revealed a structured cosmos hidden beneath the surface of YouTube's endless content stream. We've mapped galaxies bound by shared audiences, identified echo chambers and bridge channels, and exposed the black holes that shape attention flows.
    </p>
    
    <p>
        As the platform continues to evolve, so will its cosmic structure. New galaxies will form, old ones will merge or fade, and the forces of attraction will reshape the landscape in ways we can only begin to imagine.
    </p>
    
    <p>
        The YouNiverse awaits its next explorers. 🚀
    </p>
</section>
