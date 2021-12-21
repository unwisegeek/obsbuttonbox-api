from string import Template

scrollbar_template = Template(
    """
    <!-- Codes by HTML.am -->

<!-- CSS Code -->
<style>
.GeneratedMarquee {
max-width: 
font-family:'Courier New', monospace;
font-size:18px;
font-weight:bold;
line-height:1em;
text-align:left;
color:#FFCC33;
background-color:#000000;
padding:0em;

}
</style>

<!-- HTML Code -->
<marquee class="GeneratedMarquee" direction="left" scrollamount="15" behavior="alternate">$msg</marquee>
<marquee class="GeneratedMarquee" direction="right" scrollamount="15" behavior="alternate">$msg</marquee>


    """
)

scrollbar_template_orig = Template(
"""
<style>
.scroll-left {
 height: 50px;	
 overflow: hidden;
 position: relative;
 background: black;
 color: orange;
 border: 1px solid black;
}
.scroll-left p {
 position: absolute;
 width: 100%;
 height: 100%;
 margin: 0;
 line-height: 50px;
 /* text-align: center; */
 /* Starting position */
 transform:translateX(100%);
 /* Apply animation to this element */
 animation: scroll-left 10s linear infinite;
 animation-direction: alternate;
 animation-delay: 0s
}
/* Move it (define the animation) */
@keyframes scroll-left {
 0%   {
 transform: translateX(100%); 		
 }
 100% {
 transform: translateX(-80%); 
 }
}
</style>

<div class="scroll-left">
<p>$msg</p>
</div>
"""
)