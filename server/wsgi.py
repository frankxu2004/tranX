import json
from server.app import *

from components.standalone_parser import StandaloneParser

config_dict = json.load(open('server/config_conala.json', encoding='utf-8'))
config = config_dict['conala']
app.config['PARSERS'] = {'conala': StandaloneParser(parser_name=config['parser'],
                                                    model_path=config['model_path'],
                                                    example_processor_name=config['example_processor'],
                                                    beam_size=config['beam_size'],
                                                    reranker_path=config['reranker_path'],
                                                    cuda=False)}

if __name__ == "__main__":
    app.run()
