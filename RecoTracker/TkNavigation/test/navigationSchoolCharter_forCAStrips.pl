#!/usr/bin/env perl

## Navigation school plotter:
##   Takes the output of the NavigationSchoolAnalyzer, and produces a '.dot' file
##   to be visualized with graphviz (http://www.graphviz.org/)
##
## Usage:
##   - edit the NavigationSchoolAnalyzer cfg.py to select which navigation school to print
##   - run the cfg.py for the NavigationSchoolAnalyzer
##   - perl -w navigationSchoolCharter.pl detailedInfo.log > yourSchool.dot
##   - dot -Tpng -o yourSchool.png yourSchool.dot
##
## Output:
##   - red lines are 'inside-out' only (red = hot = bang = proton-proton collisions = in-out)
##   - blue lines are 'outside-in' only (blue = sky = cosmics = out-in)
##   - green lines are two-way links (with the arrow set inside-out)

use Data::Dumper;

## Parse the set of lines describing one layer
sub parseLayer {
    my $txt = shift;
    my ($be, $name) = ($txt =~ m/^(barrel|endcap) subDetector: (\w+)/m) or die "Can't parse layer block\n" . $txt . "\n";
    my ($l) = ($txt =~ m/^(?:wheel|layer): (\d+)/m) or die "Can't parse layer block\n" . $txt . "\n";
    my ($s) = ($txt =~ m/^side: (\w+)/m);
    $s = '' if $be ne "endcap";
    return sprintf('%s%s_%d', $name,$s,$l);
}

## Parse the set of lines describing all links starting from one layer
my %layers;
sub parseNavi {
   my $txt = shift;
   my $start = parseLayer($txt);
   my @outIn = (); 
   my @inOut = ();
   if ($txt =~ m/^\*\*\* INsideOUT CONNECTED TO \*\*\*\n((([a-z0-9]+.*\n)+-+\n)+)/m) {
        my $list = $1;
        #die "VVVVVVVVVVVVVVV\n$list\n^^^^^^^^^^^^^^^^^^^^\n";
        foreach (split(/---+/, $list)) { m/subDetector/ and push @inOut, parseLayer($_); }
   }
   if ($txt =~ m/^\*\*\* OUTsideIN CONNECTED TO \*\*\*\n((([a-z0-9]+.*\n)+-+\n)+)/m) {
        my $list = $1;
        #die "VVVVVVVVVVVVVVV\n$list\n^^^^^^^^^^^^^^^^^^^^\n";
        foreach (split(/---+/, $list)) { m/subDetector/ and push @outIn, parseLayer($_); }
   }
   $layers{$start} = { 'inOut' => [ @inOut ], 'outIn' => [ @outIn ] };
}

## Read input and parse it layer by layer
my $text = join('', <>);
while ($text =~ m/^(####+\nLayer.*\n([^#].*\n)+)/gm) {
    parseNavi($1);
}

#print Dumper(\%layers);

## Write the output in a graphviz syntax
print "digraph G {\n";
print "node [shape=ellipse, color=black, fillcolor=\"#EDEDED\", style=filled];\n";
foreach my $k (sort(keys(%layers))) {
    # Skip layers with "TEC" or "TOB" in their names
    next if $k =~ /TEC|TOB|TIB_3|TIB_4/;
    my $modified_name = $k;
    # Modify the name based on conditions
    $modified_name =~ s/PixelBarrel_1/BPix1/;  
    $modified_name =~ s/PixelBarrel_2/BPix2/;     
    $modified_name =~ s/PixelBarrel_3/BPix3/;     
    $modified_name =~ s/PixelBarrel_4/BPix4/;
    $modified_name =~ s/PixelEndcapMinus_1/FNPix1/;
    $modified_name =~ s/PixelEndcapMinus_2/FNPix2/;
    $modified_name =~ s/PixelEndcapMinus_3/FNPix3/;
    $modified_name =~ s/PixelEndcapPlus_1/FPPix1/;
    $modified_name =~ s/PixelEndcapPlus_2/FPPix2/;
    $modified_name =~ s/PixelEndcapPlus_3/FPPix3/;
    $modified_name =~ s/TIB_1/TIB1/;  
    $modified_name =~ s/TIB_2/TIB2/;    
    $modified_name =~ s/TIB_3/TIB3/;    
    $modified_name =~ s/TIB_4/TIB4/;
    $modified_name =~ s/TIDMinus_1/TIDN1/;
    $modified_name =~ s/TIDMinus_2/TIDN2/;
    $modified_name =~ s/TIDMinus_3/TIDN3/;
    $modified_name =~ s/TIDPlus_1/TIDP1/;
    $modified_name =~ s/TIDPlus_2/TIDP2/;
    $modified_name =~ s/TIDPlus_3/TIDP3/;

    print "$modified_name\n";

    foreach my $l1 ( @{$layers{$k}->{'inOut'}} ) {
        my $color = 'red';
        my $line_style = 'dashed';
        next if $l1 =~ /TEC|TOB|TIB_3|TIB_4/;
        my $l1modified_name = $l1;
        $l1modified_name =~ s/PixelBarrel_1/BPix1/;  
        $l1modified_name =~ s/PixelBarrel_2/BPix2/;     
        $l1modified_name =~ s/PixelBarrel_3/BPix3/;     
        $l1modified_name =~ s/PixelBarrel_4/BPix4/;
        $l1modified_name =~ s/PixelEndcapMinus_1/FNPix1/;
        $l1modified_name =~ s/PixelEndcapMinus_2/FNPix2/;
        $l1modified_name =~ s/PixelEndcapMinus_3/FNPix3/;
        $l1modified_name =~ s/PixelEndcapPlus_1/FPPix1/;
        $l1modified_name =~ s/PixelEndcapPlus_2/FPPix2/;
        $l1modified_name =~ s/PixelEndcapPlus_3/FPPix3/;
        $l1modified_name =~ s/TIB_1/TIB1/;  
        $l1modified_name =~ s/TIB_2/TIB2/;    
        $l1modified_name =~ s/TIB_3/TIB3/;    
        $l1modified_name =~ s/TIB_4/TIB4/;
        $l1modified_name =~ s/TIDMinus_1/TIDN1/;
        $l1modified_name =~ s/TIDMinus_2/TIDN2/;
        $l1modified_name =~ s/TIDMinus_3/TIDN3/;
        $l1modified_name =~ s/TIDPlus_1/TIDP1/;
        $l1modified_name =~ s/TIDPlus_2/TIDP2/;
        $l1modified_name =~ s/TIDPlus_3/TIDP3/;

        if (grep($_ eq $k, @{$layers{$l1}->{'outIn'}})) {
            $color = 'black';
            $line_style = 'solid'; 
        }
        print "\t$modified_name -> $l1modified_name [color=$color, line_style=$line_style]\n";
    }
    foreach my $l2 ( @{$layers{$k}->{'outIn'}} ) {
        my $l2modified_name = $l2;
        my $line_style = 'dashed';
        next if $l2 =~ /TEC|TOB|TIB_3|TIB_4/;
        $l2modified_name =~ s/PixelBarrel_1/BPix1/;  
        $l2modified_name =~ s/PixelBarrel_2/BPix2/;     
        $l2modified_name =~ s/PixelBarrel_3/BPix3/;     
        $l2modified_name =~ s/PixelBarrel_4/BPix4/;
        $l2modified_name =~ s/PixelEndcapMinus_1/FNPix1/;
        $l2modified_name =~ s/PixelEndcapMinus_2/FNPix2/;
        $l2modified_name =~ s/PixelEndcapMinus_3/FNPix3/;
        $l2modified_name =~ s/PixelEndcapPlus_1/FPPix1/;
        $l2modified_name =~ s/PixelEndcapPlus_2/FPPix2/;
        $l2modified_name =~ s/PixelEndcapPlus_3/FPPix3/;
        $l2modified_name =~ s/TIB_1/TIB1/;  
        $l2modified_name =~ s/TIB_2/TIB2/;    
        $l2modified_name =~ s/TIB_3/TIB3/;    
        $l2modified_name =~ s/TIB_4/TIB4/;
        $l2modified_name =~ s/TIDMinus_1/TIDN1/;
        $l2modified_name =~ s/TIDMinus_2/TIDN2/;
        $l2modified_name =~ s/TIDMinus_3/TIDN3/;
        $l2modified_name =~ s/TIDPlus_1/TIDP1/;
        $l2modified_name =~ s/TIDPlus_2/TIDP2/;
        $l2modified_name =~ s/TIDPlus_3/TIDP3/;
        next if (grep($_ eq $k, @{$layers{$l2}->{'inOut'}})) ;
        print "\t$modified_name -> $l2modified_name [color=blue, line_style=$line_style]\n";
    }
}
print "}\n";

