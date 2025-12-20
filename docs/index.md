---
layout: default
title: "YouNiverse: Voyage Through Video Galaxies"
---
<head>
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@400;700&display=swap" rel="stylesheet">
</head>


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
    
    <p>
        To answer these questions, we turned to the YouNiverse dataset—and the name truly does it justice. its size is that of a universe. -> Data from 73 million videos , 137 thousand channels and 8.6 billion comments from 449 million users on a timeframe from May 2005 to October 2019.
    </p>

    <p>
        Looking at this universe with the naked eye, we see a system that has grown exponentially since its 'big bang'. What started as a few flickering lights has evolved into a sprawling ecosystem. However, this growth is not uniform.
    </p>
    
    <div class="viz-container">
        <div id="growth-chart" class="viz-placeholder">
            {% include_relative timeline_evolution.html %}
        </div>
    </div>

    <p>
        When we peer through our telescope at these celestial bodies (channels), we notice a stark reality: size is not distributed equally. The distribution of views and subscribers follows a <strong> Power Law </strong> a mathematical signature of a "winner-takes-all" dynamic. A few 'Supermassive' channels command the vast majority of the YouNiverse's light, while millions of smaller stars twinkle in the background. The top 1% of channels capture over 46% of all views, a cosmic inequality that shapes the entire ecosystem.
    </p>


    <div class="viz-container">
        <div id="power-law-chart" class="viz-placeholder">
            {% include_relative powerlaw.html %}
        </div>
    </div>


    <p>
        To understand the nature of these stars, we first look at their "Spectra"—the content categories assigned to them. While this gives us a hint of their composition (Gaming, News, Education), categories alone don’t tell us how these stars interact.  
    </p>

    <div class="viz-container">
        <div id="category-chart" class="viz-placeholder">
            {% include_relative pie_chart.html %}
        </div>
    </div>

    <p>
        To see the true architecture of the YouNiverse, we must board our spaceship and look at the gravitational bonds between them.
    </p>
</section>

<section id="galaxies" class="section">
    <span class="section-number">Chapter III</span>
    <h2>Constructing the Cosmic Map: From Comments to Galaxies</h2>
    
    <p>
        To understand our YouNiverse, we want to see what channels actually share common audiences. By doing this we will be able to run community detection algorithms and visualize types of interactions.
    </p>
    <p>
        To do this we will use the biggest file in our dataset, the comment data. We want to know which channels users most commented on. "We establish gravitational bonds between channels: when users orbit both, commenting frequently on each, we draw a connection weighted by the strength of their shared audience. The edge of these weights will then be first determined by the number of commenters they have in common. Two channels with many shared commenters are linked by strong gravitational bonds—they orbit in the same region of the YouNiverse.
    </p>

    <div class="viz-container">
        <div id="raw-network-viz" class="viz-placeholder">
            <img src='USER1.png' width="100%">
        </div>
    </div>

    <p>
        In space, a massive sun has more gravity simply because it is big. On YouTube, two "Black Hole" channels (like PewDiePie and T-Series) might share many commenters just because they are famous, not because they are related. To find true communities, we had to "level the playing field" by normalizing our edge weights.

        We developed a Similarity Score to penalize the sheer size of a channel, ensuring that a "Galaxy" is formed by genuine audience overlap rather than just popularity.
        Imagine trying to see stars near the sun—their light is drowned out. Similarly, mega-channels like PewDiePie overshadow genuine connections. Our Similarity Score acts like a solar filter: it dims the giants proportionally to their size, revealing the authentic audience overlaps that define true communities.
    </p>
    <p>
    To see the true shape of the galaxies, we had to apply <strong>Gravitational Shielding</strong>. By using our similarity score, we effectively "muted" the blinding light of the Black Holes. This allowed us to see the faint, genuine connections between smaller stars that were previously invisible in the glare of the platform's giants. 
    </p>

    <details class="math-deep-dive" style="border: 1px solid #ffffffff; padding: 20px; border-radius: 8px; background-color: #ffffffff; margin: 20px 0;color: #000000;">
        <summary style="font-weight: bold; cursor: pointer; font-size: 1.1em;">📊 The Mathematics of Normalization (Similarity Score)</summary>
        <div class="math-content">
            <p><strong>The Problem:</strong> PewDiePie and T-Series might share 100,000 commenters simply because they each have 100 million subscribers. Meanwhile, two niche gaming channels sharing 500 commenters might have a much stronger cultural connection.</p>
            
            <p><strong>The Solution:</strong> We penalize large channels proportionally to their size:</p>
            
            $$size\_factor = \left( \frac{total\_commenters}{median\_commenters} \right)^\beta$$
            
            $$penalty(channel1, channel2) = (size\_factor(channel1) \cdot size\_factor(channel2))^\alpha$$
            
            $$Similarity\_Score = \frac{shared\_commenters}{penalty}$$

            <ul style="margin-top: 15px;">
                <li><strong>size_factor</strong>: How much larger is this channel than typical channels?</li>
                <li><strong>penalty</strong>: Expected overlap if connections were random</li>
                <li><strong>α, β</strong>: Tuning parameters (we used α=0.5, β=1)</li>
            </ul>
            
            <p><strong>Result:</strong> Two mega-channels need exponentially more shared commenters to appear "connected" than two small channels. This reveals genuine communities rather than just popularity contests.</p>
        </div>
    </details>

    

    <p>
        With our normalized map in hand, we applied the Louvain Community Detection algorithm. Think of this as a way to find where the "gas clouds" of users naturally condense into distinct structures.
    </p>

    <div class="insight-box" style="background: #132f34ff; padding: 15px; border-left: 4px solid #17a2b8; margin: 20px 0;color: #ffffff">
    ✨ <strong>The Breakthrough:</strong> With gravitational shielding applied, distinct galaxies emerge from the chaos. Each represents a true audience community bound by shared interests, not just shared fame.
    </div>
    <p>
        Louvain seeks to maximize Modularity—a metric that measures how much "denser" the connections are within a galaxy compared to a random universe. Our map achieved a Modularity score of 0.655.
        In the world of network science, a score above 0.5 is a significant discovery. It confirms that the YouNiverse is not a chaotic cloud of random stars, but a structured system of distinct, high-density galaxies bound by shared cultures, languages, and interests.
    </p>


    <h2>The Architecture of the YouNiverse</h2>
    
    <p>
        By applying the Louvain algorithm, we successfully charted <span class="highlight">52 distinct communities</span> within the cosmic map. It became immediately clear that this universe is highly polarized: while some regions are vast, mainstream <strong>Super-Galaxies</strong>, others are small, isolated <strong>Niche Constellations</strong>. 
    </p>

    <p>
        The scale varies dramatically, the smallest of these communities contain as few as two channels, existing like distant binary stars in the deep void of the YouNiverse.
    </p>
    <p>
        Before diving deeper, let's label our communities with the biggest channel in each. This gives us the first valuable insights into what sort of galaxies is there in the YouNiverse.
    </p>

    <div class="viz-network">
        <div class="viz-title">The 52 Galaxies of the YouNiverse</div>
        <div id="full-network-viz" class="viz-placeholder">
            <iframe src="./a.html" width="100%" height="500px" frameborder="0"></iframe>
        </div>
    </div>
        <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">52</div>
            <div class="stat-label">Galaxies Detected</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">0</div>.<div class="stat-number">655</div>
            <div class="stat-label">Modularity Score</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">80</div><div class="stat-number">%</div>
            <div class="stat-label">Channels in Top 5 Galaxies</div>
        </div>
    </div>


    <h3>The Core vs. The Periphery</h3>
    <p>
        In the center of our map lies the <strong>Galactic Core</strong>. Here, the mainstream galaxies are so massive and their audiences so interconnected that their borders often blur together. Yet, despite this density, the Louvain algorithm reveals they remain distinct cultural entities with their own centers of gravity.
    </p>

    <p>
        Stretching out from this core are thin, elongated edges : the <strong>Interstellar Bridges</strong>. These represent bridge channels that link the mainstream center to peripheral niche clusters. These channels serve as the connective tissue of the YouNiverse, allowing users to travel between vastly different content worlds.
    </p>

    <div class="quote">
        "The YouNiverse is not a single mass, but a complex web where the mainstream core and niche satellites are held together by the gravity of shared audiences."
    </div>

    <h3>A Voyage into the Core</h3>
    <p>
        To understand the internal divisions of the most dominant communities, we must look past the "space dust" of the periphery. By zooming into the core, we can observe the fine-tuned interactions and sub-galaxies that shape the most popular regions of YouTube.
    </p>

    <div class="viz-network">
        <div class="viz-title">Core Exploration Map </div>
        <p style="font-size: 0.9em; color: #666;text-align: center;">
            Showing the 5 biggest galaxies, those that form the core of our universe.
        </p>
        <div id="interactive-core-viz">
            <iframe src="./b.html" width="100%" height="500px" frameborder="0" style="border:none; display: block;"></iframe>
        </div>
    </div>

    <h3>What We've Discovered</h3>
    <p>
        By building our cosmic map from 8.6 billion comments across 137,000 channels, we've revealed something remarkable: <strong>YouTube isn't a chaotic cloud of random content</strong>. It's a structured universe with 52 distinct cultural galaxies, each with its own centers of gravity, its own audiences, and its own identity.
    </p>

    <p>
        The modularity score of 0.655 confirms what we suspected: users don't wander randomly across YouTube. They orbit within specific communities, occasionally traveling between galaxies through bridge channels, but largely remaining within their cultural home.
    </p>

    <p>
        With our map complete, we can now begin the real voyage: <strong>descending into each galaxy to meet its inhabitants, understand its culture, and trace the journeys of travelers between worlds.</strong>
    </p>

    <div class="quote">
        "The YouNiverse is not a single universe, but a multiverse, 52 parallel worlds occupying the same digital space, each invisible to the others unless you know where to look."
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
