This directory is a testing environment for testing out PSS.py


Make sure you have the following directories for PSS_Runner to work
  parsed_docs/
  raw_docs/
  PSS/

Make sure raw_doc/s has some one-level directories with files in them
  to process

Make sure you have the following files in the right directories:
  config.toml
  stopwords.txt
  parsed_docs/file.toml
  PSS/PSS.py
  PSS/__init__.py

Note: run example.py within the same directory you have the above
  files and directories within.  a directory idx/ will also be 
  created in the directory you run example.py

Note: you if you accidentally delete parsed_docs/file.toml, simply
  copy backup_file.toml into parsed_docs/ and rename it to file.toml

