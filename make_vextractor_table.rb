require 'rubygems'
require 'byebug'

venoms = IO.readlines("venoms_trimmed_pass1.txt")
effects = IO.readlines("effects_trimmed_pass1.txt")

venoms_array = []
venoms.each do |ven|
  ven_arr = ven.split('|')
  venoms_array.push([ven_arr[1].chomp, ven_arr[0]])
end

effects_array = []
effects.each do |eff|
  eff_arr = eff.split('|')
  effects_array.push([eff_arr[1].chomp, eff_arr[0]])
end

list_of_possible_venoms = venoms_array.map { |x| x[0] }.uniq

output_string = ""
output_string << "venom|effect|pmid\n"

list_of_possible_venoms.each do |compound|
  pmids_for_compound = []
  venoms_array.collect{ |v| pmids_for_compound.push(v[1]) if (v[0] == compound) }
  pmids_for_compound.each do |pmid|
    effects_for_compound = []
    effects_array.collect{ |e| effects_for_compound.push(e[0]) if (e[1] == pmid) }
    effects_for_compound.each { |effect| output_string << "#{compound}|#{effect}|#{pmid}\n" }
  end
end

File.open("autoparse_results.csv", 'w') { |f| f.write(output_string) }
