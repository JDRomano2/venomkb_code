#!/usr/bin/env ruby

# See OptionParser documentation on ruby-doc.org: http://ruby-doc.org/stdlib-2.1.4/libdoc/optparse/rdoc/OptionParser.html

require 'optparse'
require 'optparse/time'
require 'ostruct'

class SMDB_options

  # Return a structure describing the options:
  def self.parse(args)
    # First, set default options
    # Options are collected in `options`
    options = OpenStruct.new()
    options.config = "/etc/my.cnf"
    options.search_fields = {}
    options.show_predications = false
    options.verbose = false
    options.suppress_output = false

    opt_parser = OptionParser.new do |opts|
      opts.banner = "Usage: smdb_search.rb [options]"
      
      opts.separator ""
      opts.separator "Specific options:"

      #Mandatory
      opts.on("-c", "--config-file [FILE]",
              "Import MySQL config file for connecting to SemMedDB (default '/etc/my.cnf')") do |conf|
        options.config = conf
      end

      opts.on("--cui [CUI]", String, "UMLS CUI or GO ID") do |cui|
        options.search_fields[:cui] = cui
      end

      opts.on("--predicate [PREDICATE]", String, "A predicate that is indexed by SemMedDB") do |pred|
        options.search_fields[:predicate] = pred
      end

      opts.on("--preferred-name [PREFERRED_NAME]", String, "The preferred name for a UMLS or GO concept") do |pref|
        options.search_fields[:preferred_name] = pref
      end

      opts.on("-m", "--pmid [PUBMED ID]", String, "The PMID for an article that you want to extract predications from.") do |m|
        options.search_fields[:pmid] = m
      end

      opts.on("-f", "--pmids-file [FILE]", String, "Path to a file containing a list of PMIDs. Will search for all predications in all PMIDs, returning a \"bag-of-words\" of concepts.") do |f|
        options.search_fields[:pmids_file] = f
      end

      opts.on("-p", "--show-predications", "Show predications that match concept and predicate") do |p|
        options.show_predications = p
      end

      opts.on("-v", "--verbose", "Give output of each MySQL query") do |v|
        options.verbose = v
      end

      opts.on("-s", "--suppress-output", "Only the final results are printed to STDOUT - useful for piping output") do |s|
        options.suppress_output = s
      end

      opts.on_tail("-h", "--help", "Show this message") do
        puts opts
        exit
      end
    end

    opt_parser.parse!(args)
    options
  end

end
