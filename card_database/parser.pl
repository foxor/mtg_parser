#!/usr/bin/env perl

#open(TF, "<testfile");
open(TF, "<wget.out");
open(CA, ">cardtext.sql");
print CA "DROP TABLE IF EXISTS cards;\n";
print CA "CREATE TABLE cards (\n";
print CA "  multiverse_id INT NOT NULL PRIMARY KEY,\n";
print CA "  card_name CHAR(64),\n";
print CA "  mana_cost CHAR(128),\n";
print CA "  converted_mana_cost INT,\n";
print CA "  power CHAR(4),\n";
print CA "  toughness CHAR(4),\n";
print CA "  loyalty INT,\n";
print CA "  hand_mod INT,\n";
print CA "  life_mod INT,\n";
print CA "  rarity CHAR(16),\n";
print CA "  artist CHAR(32)\n";
print CA ");\n";
print CA "DROP TABLE IF EXISTS types;\n";
print CA "CREATE TABLE types (\n";
print CA "  card INT NOT NULL,\n";
print CA "  type CHAR(32),\n";
print CA "  FOREIGN KEY (card) REFERENCES cards(multiverse_id)\n";
print CA ");\n";
print CA "DROP TABLE IF EXISTS rules_text;\n";
print CA "CREATE TABLE rules_text (\n";
print CA "  card INT NOT NULL,\n";
print CA "  flavor BOOL,\n";
print CA "  text TEXT,\n";
print CA "  FOREIGN KEY (card) REFERENCES cards(multiverse_id)\n";
print CA ");\n";
#types is a FK
#card_text is a FK
#expansion, other_sets, community_rating are throwaway
$current_card = 0;
while (<TF>) {
  if (m/Discussion.aspx\?multiverseid=(\d*)"/ && !m/Click/) {
    print CA "INSERT INTO `cards` (multiverse_id) VALUES ($1);\n";
    $current_card = $1;
  } elsif (m/^\s*([\w\s\/]*):<\/div>/) {
    my $fieldname = lc($1);
    $fieldname =~ s/ /_/g;
    if ($fieldname =~ m/(expansion|other_sets|community_rating)/) {
      next;
    }
    $line = <TF>;
    $line = <TF>;
    $line =~ s/<img .*?alt="(.*?)".*? \/>/[[[\1]]]/g;
    $line =~ s/\"?<\/?i>\"?//g;
    $line =~ s/\xe2\x80\x94/-/g;
    $line =~ s/"/\\"/g;
    if ($line =~ m/<div class=\\"cardtextbox\\">/) {
      $fieldname = ($fieldname =~ m/flavor_text/) ? "1" : "0";
      while ($line =~ /<div class=\\"cardtextbox\\">(.+?)<\/div>/g) {
        print CA "INSERT INTO `rules_text` VALUES ($current_card, $fieldname, \"$1\");\n";
      }
    } else {
      $line =~ s/<.*?>//g;
      $line =~ s/^\s*(.*?)\s*$/\1/g;
      if ($fieldname =~ m/types/) {
        while ($line =~ /(\w+)/g) {
          print CA "INSERT INTO `types` VALUES ($current_card, \"$1\");\n";
        }
      } elsif ($fieldname =~ m/p\/t/) {
        $line =~ /(\d*\*?) \/ (\d*\*?)/;
        print CA "UPDATE `cards` SET power=\"$1\" WHERE multiverse_id=$current_card;\n";
        print CA "UPDATE `cards` SET toughness=\"$2\" WHERE multiverse_id=$current_card;\n";
      } elsif ($fieldname =~ m/hand\/life/) {
        $line =~ /\(Hand Modifier: \+?(-?\d+)&nbsp;,&nbsp;Life Modifier: \+?(-?\d+)\)/;
        print CA "UPDATE `cards` SET hand_mod=$1 WHERE multiverse_id=$current_card;\n";
        print CA "UPDATE `cards` SET life_mod=$2 WHERE multiverse_id=$current_card;\n";
      } else {
        print CA "UPDATE `cards` SET $fieldname=\"$line\" WHERE multiverse_id=$current_card;\n";
      }
    }
  }
}
