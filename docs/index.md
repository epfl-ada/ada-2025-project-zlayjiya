---
layout: default
title: "YouNiverse: Voyage Through Video Galaxies"
---
<head>
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
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
        To answer these questions, we turned to the YouNiverse dataset. And the name truly does it justice, its size is that of a universe. Data from 73 million videos , 137 thousand channels and 8.6 billion comments from 449 million users on a timeframe from May 2005 to October 2019. The dataset claims to only hold data from english speaking videos (more on that later).
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
        When we peer through our telescope at these celestial bodies (channels), we notice a stark reality: size is not distributed equally. The distribution of views and subscribers follows a power law, a mathematical signature of winner-takes-all dynamics commonly observed in large-scale social systems. A few 'Supermassive' channels command the vast majority of the YouNiverse's light, while millions of smaller stars twinkle in the background. The top 1% of channels capture over 46% of all views, a cosmic inequality that shapes the entire ecosystem.
    </p>


    <div class="viz-container">
        <div id="power-law-chart" class="viz-placeholder">
            {% include_relative powerlaw.html %}
        </div>
    </div>


    <p>
        To understand the nature of these stars, we first look at their "Spectra"—the content categories assigned to them. This provides a first-order view of what content dominates the YouNiverse, before asking how these channels interact. While this gives us a hint of their composition (Gaming, News, Education), categories alone don’t tell us how these stars interact.  
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
        To understand our YouNiverse, our objective to see what channels actually share common audiences. By doing this we will be able to run community detection algorithms and visualize types of interactions.
    </p>
    <p>
        To do this we will use the biggest file in our dataset, the comment data. We want to know which channels users most commented on. "We establish gravitational bonds between channels: when users orbit both, commenting frequently on each, we draw a connection weighted by the strength of their shared audience. The edge of these weights will then be first determined by the number of commenters they have in common. Two channels with many shared commenters are linked by strong gravitational bonds—they orbit in the same region of the YouNiverse.
    </p>

    <div class="viz-container">
        <div id="raw-network-viz" class="viz-placeholder">
            <img src='USER1.png' width="100%">
        </div>
    </div>
    <div style="text-align: center; margin-top: 10px; font-family: sans-serif;">
        <p style="font-size: 1.2rem; color: #989292ff; max-width: 600px; margin: 0 auto; line-height: 1.4;">
            Demonstration of graph creation using <strong>the top 3 channels </strong> of the user.
        </p>
    </div>

    <h3>Normalizing the gravitational bonds</h3>
    <p>
        In space, a massive sun has more gravity simply because it is big. On YouTube, two "Black Hole" channels (like PewDiePie and T-Series) might share many commenters just because they are famous, not because they are related. To find true communities, we had to "level the playing field" by normalizing our edge weights.

        We developed a Similarity Score to penalize the sheer size of a channel, ensuring that a "Galaxy" is formed by genuine audience overlap rather than just popularity.
        Imagine trying to see stars near the sun—their light is drowned out. Similarly, mega-channels like PewDiePie overshadow genuine connections. Our Similarity Score acts like a solar filter: it dims the giants proportionally to their size, revealing the authentic audience overlaps that define true communities.
    </p>
    <p>
    To see the true shape of the galaxies, we had to apply <strong>Gravitational Shielding</strong>. By using our similarity score, we effectively "muted" the blinding light of the Black Holes. This allowed us to see the faint, genuine connections between smaller stars that were previously invisible in the glare of the platform's giants. 
    </p>

    <details class="math-deep-dive" style="border: 1px solid rgba(139, 92, 246, 0.3); padding: 20px; border-radius: 8px; background-color: rgba(40, 40, 40, 0.6); backdrop-filter: blur(10px); margin: 20px 0; color: #e8e8f0; font-family: '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
    <summary style="font-weight: bold; cursor: pointer; font-size: 1.1em; color: #ffffffff; outline: none;">📊 The Mathematics of Normalization (Similarity Score)</summary>
    
    <div class="math-content" style="margin-top: 20px; padding-left: 25px; color: #a0a0c0; border-left: 2px solid rgba(139, 92, 246, 0.3);">
        <p style="margin-bottom: 12px;"><strong style="color: #ffffff;">The Problem:</strong> PewDiePie and T-Series might share 100,000 commenters simply because they each have 100 million subscribers. Meanwhile, two niche gaming channels sharing 500 commenters might have a much stronger cultural connection.</p>
        
        <p style="margin-bottom: 12px;"><strong style="color: #ffffff;">The Solution:</strong> We penalize large channels proportionally to their size:</p>
        
        <div style="background: rgba(0, 0, 0, 0.2); padding: 15px; border-radius: 6px; margin: 15px 0; text-align: center; color: #ffffff;">
            <p style="margin: 10px 0;">$$size\_factor = \left( \frac{total\_commenters}{median\_commenters} \right)^\beta$$</p>
            <p style="margin: 10px 0;">$$penalty(c_1, c_2) = (size\_factor(c_1) \cdot size\_factor(c_2))^\alpha$$</p>
            <p style="margin: 10px 0;">$$Similarity\_Score = \frac{shared\_commenters}{penalty}$$</p>
        </div>

        <ul style="margin-top: 15px; list-style-type: none; padding-left: 0;">
            <li style="margin-bottom: 8px;"><strong style="color: #06b6d4;">size_factor</strong>: How much larger is this channel than typical channels?</li>
            <li style="margin-bottom: 8px;"><strong style="color: #06b6d4;">penalty</strong>: Expected overlap if connections were random.</li>
            <li style="margin-bottom: 8px;"><strong style="color: #06b6d4;">α, β</strong>: Tuning parameters (we used α=0.5, β=1).</li>
        </ul>
        
        <p style="margin-top: 15px; line-height: 1.6;">
            <strong style="color: #8b5cf6;">Result:</strong> Two mega-channels need exponentially more shared commenters to appear "connected" than two small channels. This reveals genuine communities rather than just popularity contests.
        </p>
    </div>
    </details>


    <h3>Filtering the Cosmic Noise</h3>
    <p>
        Even with gravitational shielding applied, our universe still contained faint, unreliable connections, like distant radio signals lost in static. To build a clean map of meaningful relationships, we applied two critical filters to remove the cosmic noise.
    </p>

    <div class="insight-box" style="background: #1a1a2e; padding: 20px; border-left: 4px solid #ffd54f; margin: 20px 0; color: #ffffff; border-radius: 4px;">
        <strong>🔧 The Filtering Strategy:</strong>
        <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
            <li><strong>Minimum Subscribers Filter:</strong> We excluded channels below 200,000 subscribers. These "proto-stars" haven't yet established stable audiences, making their connections unreliable indicators of community structure.</li>
            <li><strong>Minimum Edge Weight Filter:</strong> We removed edges with fewer than 25 shared commenters. Like eliminating background radiation, this ensures we only map gravitational bonds strong enough to define true communities.</li>
        </ul>
    </div>

    <p>
        Why these thresholds? Two reasons, aside from computational efficiency. Because of our top-5 channels logic, small channels frequently had very few shared commenters and by consequence too few edges for the analysis to actually be significant. Similarly, small weight edges were not consequential given the size of the dataset and the remaining channels. Through iterative testing, we have found out that the two chosen hyperparameters were the best balance to get meaningful communities.
    </p>

    <details class="math-deep-dive" style="border: 1px solid rgba(139, 92, 246, 0.3); padding: 20px; border-radius: 8px; background-color: rgba(40, 40, 40, 0.6); backdrop-filter: blur(10px); margin: 20px 0; color: #e8e8f0; font-family: '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <summary style="font-weight: bold; cursor: pointer; font-size: 1.1em; color: #ffffffff; outline: none;">📊 Impact of Filtering on Network Structure</summary>
    
    <div class="math-content" style="margin-top: 20px; padding-left: 25px; color: #a0a0c0; border-left: 2px solid rgba(6, 182, 212, 0.2);">
        <p style="margin-bottom: 10px;"><strong style="color: #ffffff;">Before Filtering:</strong></p>
        <ul style="margin-bottom: 20px; list-style-type: none; padding-left: 0;">
            <li style="margin-bottom: 5px;">• Nodes (channels): 129,996</li>
            <li style="margin-bottom: 5px;">• Edges (connections): 32,408,399</li>
        </ul>
        
        <p style="margin-bottom: 10px;"><strong style="color: #ffffff;">After Filtering:</strong></p>
        <ul style="margin-bottom: 20px; list-style-type: none; padding-left: 0;">
            <li style="margin-bottom: 5px;">• Nodes (channels): 19,129</li>
            <li style="margin-bottom: 5px;">• Edges (connections):572,732</li>
        </ul>
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
        To understand the internal divisions of the most dominant communities, we must look past the "space dust" of the periphery. By zooming into the core, we can observe the fine-tuned interactions and galaxies that shape the most popular regions of YouTube.
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
    <h3>First Contact: A Glimpse Into Three Galaxies</h3>
    <p>
        Before we systematically analyze all galaxies, let's descend into three interesting, yet very small compared to the size of the major galaxies, ones. We will quickly analyze what sort of channels lie in them to determine how they came to be. They define three contrasting types of communities. Do not hesitate to click on the little nodes to get the names of the channels and their total strength in the graph.
    </p>

    <!-- Galaxy 1: Graph Left, Text Right -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: center; margin: 40px 0; height: 400px; padding: 30px; background: linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%); border-radius: 16px; border: 2px solid rgba(100, 181, 246, 0.3);">
        
        <div class="viz-network" >
            <!-- Insert your galaxy visualization here -->
            <iframe src="./galaxy_25.html" width="100%" height="300px" frameborder="0"></iframe>
        </div>
        
        <div>
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="font-size: 2.5em; margin-right: 15px;">🎾</div>
                <div>
                    <h4 style="color: #64b5f6; margin: 0;">Tennis Terror</h4>
                    <p style="color: #aaa; font-size: 0.9em; margin: 5px 0 0 0;">
                        Galaxy #25 • 6 channels • Biggest channel : Tennis TV
                    </p>
                </div>
            </div>
            <p style="color: #ddd; line-height: 1.7; margin-bottom: 15px;">
                A small, tight-knit community around a passion for one sport : Tennis.  
            </p>
            
        </div>
        
    </div>

    <!-- Galaxy 2: Text Left, Graph Right -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: center; margin: 40px 0; height: 400px;padding: 30px; background: linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%); border-radius: 16px; border: 2px solid rgba(171, 71, 188, 0.3);">
        
        <div>
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="font-size: 2.5em; margin-right: 15px;">🇲🇦🇹🇳</div>
                <div>
                    <h4 style="color: #ab47bc; margin: 0;">Maghrebi Power</h4>
                    <p style="color: #aaa; font-size: 0.9em; margin: 5px 0 0 0;">
                        Galaxy #25 • 32 channels • Biggest channel : 7liwa
                    </p>
                </div>
            </div>
            <p style="color: #ddd; line-height: 1.7; margin-bottom: 15px;">
                A single galaxy with what seems to be two different galaxies connected by two heavily interacting channels. Quick overview of these channels leads us to see that on one part we have some Moroccan singers and on the other side Tunisian ones.
            </p>
        </div>
        
        <div class="viz-network">
            <!-- Insert your galaxy visualization here -->
            <iframe src="./galaxy_26.html" width="100%" height="300px" frameborder="0"></iframe>
        </div>
        
    </div>

    <!-- Galaxy 3: Graph Left, Text Right -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; align-items: center; margin: 40px 0; padding: 30px; background: linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%); border-radius: 16px; height: 400px;border: 2px solid rgba(255, 193, 7, 0.3);">
        
    <div class="viz-network">
        <!-- Insert your galaxy visualization here -->
        <iframe src="./galaxy_24.html" width="100%" height="300px" frameborder="0"></iframe>
        <!-- OR -->
        <!-- <img src="galaxy_news.png" width="100%" style="border-radius: 8px;"> -->
    </div>
    
    <div>
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <div style="font-size: 2.5em; margin-right: 15px;">🏴󠁧󠁢󠁥󠁮󠁧󠁿</div>
            <div>
                <h4 style="color: #ffc107; margin: 0;">English Learners</h4>
                <p style="color: #aaa; font-size: 0.9em; margin: 5px 0 0 0;">
                    Galaxy #24 • 45 channels • Biggest channel : Go Natural English
                </p>
            </div>
        </div>
        <p style="color: #ddd; line-height: 1.7; margin-bottom: 15px;">
            Probably a hub for recharging your spacecraft before going exploring. This is a community based around learning the biggest language on the website (and the world), English. 
        </p>

    </div>
    
    </div>

    <div class="quote">
        "From isolated echo chambers to sprawling hubs, each galaxy reveals a different way communities form and interact."
    </div>

    <p>
        These three examples showcase the diversity we've discovered. In the next chapter, we will systematically analyze what truly distinguishes all major galaxies in the YouNiverse.
    </p>
    <h3>What We've Discovered</h3>
    <p>
        By building our cosmic map from 8.6 billion comments across 19,000 channels, we've revealed something remarkable: <strong>YouTube isn't a chaotic cloud of random content</strong>. It's a structured universe with 52 distinct cultural galaxies, each with its own centers of gravity, its own audiences, and its own identity.
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
    
    <p>
        We've mapped 52 galaxies, but what makes each one unique? YouTube assigns categories to channels, but these official labels only scratch the surface. A "Music" galaxy in one region might be entirely different from another. To truly understand each galaxy's identity, we need to look deeper: into the <span class="highlight">content itself</span>, the <span class="highlight">language</span>, and the <span class="highlight">behavior</span> of its inhabitants.
    </p>

    <h3>Reading the Stars: Topic Detection with LDA</h3>
    <p>
        We deployed <strong>Latent Dirichlet Allocation (LDA)</strong> on video titles and descriptions from the 10 largest galaxies. Using POS-filtering (nouns, proper nouns, adjectives) and bigram detection, we extract the hidden thematic structure within each community—the actual topics people talk about, not just the labels YouTube assigns.
    </p>
    
    <p>
        The results largely validate YouTube's categorization while revealing rich subcultures within each galaxy. Regional ecosystems also emerge, with entire non-English communities thriving in an allegedly "English-only" dataset.
    </p>

    <div class="viz-container">
        <div id="topic-explorer-container">
            <iframe src="./topic_explorer.html" width="100%" height="480px" frameborder="0" style="border:none;"></iframe>
        </div>
    </div>

    <h3>The Language Barrier: Regional Galaxies Emerge</h3>
    <p>
        One striking discovery: <span class="highlight">language creates galaxies</span>. Despite the YouNiverse dataset claiming to contain only "English-speaking" content, our analysis reveals massive non-English communities bound together by shared language.
    </p>

    <div class="insight-box" style="background: #1a1a2e; padding: 20px; border-left: 4px solid #8b5cf6; margin: 20px 0; color: #ffffff; border-radius: 4px;">
        <strong>🌍 Language-Based Galaxies Discovered:</strong>
        <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
            <li><strong>🇮🇳 Galaxy #0 - Indian Entertainment Hub (3,187 channels):</strong> Bollywood dominates (Filmfare, Salman Khan, Varun Dhawan). Hindi beauty tips, Navratri celebrations, and PUBG Mobile.</li>
            <li><strong>🇵🇭 Galaxy #7 - Filipino Entertainment Hub (596 channels):</strong> Mobile Legends: Bang Bang is the gravitational center. ABS-CBN content, Himig Handog music, and Filipino language (ang, lang, ako, ikaw).</li>
        </ul>
    </div>

    <p>
        These linguistic gravitational bonds are so strong that they override thematic connections. An Indian gamer has more in common with an Indian news channel than with an American gamer—at least in terms of shared audience.
    </p>

    <div class="quote">
        "In the YouNiverse, language isn't just communication—it's gravity. Speakers of the same language orbit together, regardless of content type."
    </div>

    <h3>Categories Confirmed: LDA Validates YouTube Labels</h3>
    <p>
        Interestingly, our LDA analysis largely <span class="highlight">confirms YouTube's category assignments</span>. The detected topics align remarkably well with the official labels:
    </p>

    <div class="insight-box" style="background: #1a1a2e; padding: 20px; border-left: 4px solid #10b981; margin: 20px 0; color: #ffffff; border-radius: 4px;">
        <strong>✅ Category-Topic Alignment:</strong>
        <ul style="margin: 10px 0 0 20px; line-height: 1.8;">
            <li><strong>Galaxy #1 (Gaming 48%):</strong> GTA mods, Roblox, Minecraft roleplay ✓</li>
            <li><strong>Galaxy #2 (Music 64%):</strong> Ariana Grande, Nicki Minaj, chill playlists ✓</li>
            <li><strong>Galaxy #3 (Howto & Style 31%):</strong> Vlogs, makeup tutorials, hauls ✓</li>
            <li><strong>Galaxy #9 (Autos & Vehicles 42%):</strong> Car reviews, bikes, off-road ✓</li>
        </ul>
    </div>

    <p>
        This validates that <strong>co-commenting behavior reflects genuine content affinity</strong>. Users who comment together genuinely share interests that match the channel's official category—the community structure is real.
    </p>

    <h3>Behavioral Signatures: How Galaxies Engage</h3>
    <p>
        Beyond topics, each galaxy has a distinct <span class="highlight">behavioral fingerprint</span>. By analyzing engagement metrics across millions of videos, we uncovered dramatically different patterns of audience interaction.
    </p>

    <div class="viz-container">
        <div id="engagement-metrics-viz">
            <iframe src="./engagement_metrics.html" width="100%" height="560px" frameborder="0" style="border:none;"></iframe>
        </div>
    </div>

    <h3>The Engagement Paradox</h3>
    <p>
        Our analysis reveals a fascinating paradox: <strong>the most-viewed content isn't the most engaging</strong>.
    </p>

    <!-- Engagement insights grid -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 30px 0;">
        
        <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(40, 30, 20, 0.8) 100%); border: 2px solid rgba(245, 158, 11, 0.4); border-radius: 12px; padding: 25px;">
            <div style="font-size: 2em; margin-bottom: 10px;">🏆</div>
            <h4 style="color: #f59e0b; margin: 0 0 10px 0;">Most Engaged: Galaxy #3 - Vlogs & Lifestyle</h4>
            <p style="color: #e2e2ed; font-size: 0.95em; margin: 0;">
                <strong>26.9 likes per 1000 views</strong><br>
                Makeup tutorials, hauls, and vlogs create devoted communities. These viewers don't just watch—they comment, share tips, and build relationships with creators.
            </p>
        </div>
        
        <div style="background: linear-gradient(135deg, rgba(20, 184, 166, 0.2) 0%, rgba(20, 40, 40, 0.8) 100%); border: 2px solid rgba(20, 184, 166, 0.4); border-radius: 12px; padding: 25px;">
            <div style="font-size: 2em; margin-bottom: 10px;">👁️</div>
            <h4 style="color: #14b8a6; margin: 0 0 10px 0;">The Viral Void: Galaxy #8 - ASMR & Kids</h4>
            <p style="color: #e2e2ed; font-size: 0.95em; margin: 0;">
                <strong>133K median views, only 4.0 engagement</strong><br>
                Slime, soap cutting, and satisfying compilations—optimized for the algorithm, not connection. Viewers consume passively without forming lasting communities.
            </p>
        </div>
        
    </div>

    <h3>Duration Tells a Story</h3>
    <p>
        Video length isn't random—it reflects the <span class="highlight">content type</span> and <span class="highlight">audience expectations</span> of each galaxy.
    </p>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">18.3</div>
            <div class="stat-label">min - Galaxy #5 Fitness<br>(Workout videos, vegan recipes)</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">8.0</div>
            <div class="stat-label">min - Galaxy #2 Pop Music<br>(Music videos, playlists)</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">16.1</div>
            <div class="stat-label">min - Galaxy #1 Gaming<br>(Let's plays, GTA mods)</div>
        </div>
    </div>

    <p>
        <strong>Fitness content (Galaxy #5)</strong> demands the longest attention—Buff Dudes workouts, vegan recipes, and Law of Attraction manifestation videos average 18+ minutes. <strong>Pop Music (Galaxy #2)</strong> lives in quick 8-minute bursts: music videos and playlist compilations.
    </p>

    <h3>The Galaxy Classification System</h3>
    <p>
        Combining topic analysis and behavioral metrics, we can classify our galaxies into distinct types:
    </p>

    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 30px 0;">
        <div style="background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4); border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 2.5em;">🌐</div>
            <h4 style="color: #8b5cf6; margin: 10px 0 5px 0;">Global Galaxies</h4>
            <p style="color: #a0a0c0; font-size: 0.85em; margin: 0;">#1 Gaming, #2 Music, #8 ASMR<br>Content transcends language</p>
        </div>
        <div style="background: rgba(236, 72, 153, 0.15); border: 1px solid rgba(236, 72, 153, 0.4); border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 2.5em;">🗣️</div>
            <h4 style="color: #ec4899; margin: 10px 0 5px 0;">Regional Galaxies</h4>
            <p style="color: #a0a0c0; font-size: 0.85em; margin: 0;">#0 Indian, #7 Filipino<br>Bound by language</p>
        </div>
        <div style="background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.4); border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 2.5em;">🎯</div>
            <h4 style="color: #06b6d4; margin: 10px 0 5px 0;">Engaged Galaxies</h4>
            <p style="color: #a0a0c0; font-size: 0.85em; margin: 0;">#3 Vlogs, #5 Fitness<br>High engagement, tight communities</p>
        </div>
    </div>

    <div class="quote">
        "Identity in the YouNiverse is multi-dimensional: what you talk about, what language you speak, how long you watch, and how much you engage all combine to define your galactic home."
    </div>

    <h3>What We've Learned About Galaxy Identity</h3>
    <p>
        Our deep dive into the 10 largest galaxies reveals that <strong>YouTube's official categories are only part of the story</strong>. The true identity of a galaxy emerges from the intersection of:
    </p>
    <ul style="color: #e2e2ed; line-height: 2;">
        <li><strong>Thematic content:</strong> What topics dominate the conversation</li>
        <li><strong>Language:</strong> The gravitational force that binds regional communities</li>
        <li><strong>Engagement patterns:</strong> Active fans vs. passive consumers</li>
        <li><strong>Content format:</strong> Long-form immersion vs. short-form consumption</li>
    </ul>
    
    <p>
        With the identity of each galaxy now mapped, our next question becomes: <strong>how do travelers move between these worlds?</strong> Do they stay loyal to their home galaxy, or do they explore the broader universe?
    </p>
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
