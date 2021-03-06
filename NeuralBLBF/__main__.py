import argparse
import torch
import logging
import json
import os
import numpy as np

from NeuralBLBF.evaluate import run_test_set
from NeuralBLBF.train import train
from NeuralBLBF.model import TinyEmbedFFNN, SmallEmbedFFNN, SparseLinear, \
                             LargeEmbedFFNN, CrossNetwork, SparseFFNN


if __name__ == "__main__":
    logging.basicConfig(level="INFO", format="%(asctime)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--mode', default='train', choices=['train', 'test'])

    # Paths to datasets
    parser.add_argument('--train', default='data/vw_compressed_train')
    parser.add_argument('--valid', default='data/vw_compressed_validate')
    parser.add_argument('--test', default='data/vw_compressed_validate')
    parser.add_argument('--stop_idx', type=int, default=1000000)
    parser.add_argument('--step_size', type=int, default=100000)
    parser.add_argument('--device_id', type=int, default=1)
    parser.add_argument('--feature_dict_name', type=str,
                        default='data/features_to_keys.json')

    # Parameters related to training
    parser.add_argument('--lamb', type=float, default=1)
    parser.add_argument('--gamma', type=float, default=0)
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--learning_rate', type=float, default=0.00005)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--enable_cuda', action='store_true')
    parser.add_argument('--training_eval', action='store_true',
                        help="Also perform evaluation on training set")
    parser.add_argument('--weight_decay', type=float, default=0)

    # Parameters related to the layout of the network
    parser.add_argument('--model_type', default="TinyEmbedFFNN",
                        choices=["TinyEmbedFFNN", "SmallEmbedFFNN", "SparseLinear",
                                 "LargeEmbedFFNN", "CrossNetwork", "SparseFFNN"])
    parser.add_argument('--sparse', action='store_true')
    parser.add_argument('--embedding_dim', type=int, default=20)
    parser.add_argument('--hidden_dim', type=int, default=100)
    parser.add_argument('--dropout', type=float, default=0)

    # Parameters related to loading or storing models
    parser.add_argument('--resume', type=str, default=None)
    parser.add_argument('--save', action='store_true')
    parser.add_argument('--save_model_path', type=str, default='data/models')


    args = vars(parser.parse_args())

    if args['enable_cuda'] and torch.cuda.is_available():
        device = torch.device('cuda', args['device_id'])
    else:
        device = None

    logging.info("Parameters:")
    for k, v in args.items():
        logging.info("  %12s : %s" % (k, v))

    # Load dict mapping features to keys
    with open(args['feature_dict_name']) as f: feature_dict = json.load(f)
    if not os.path.exists(args['save_model_path']):
        os.mkdir(args['save_model_path'])

    args['save_model_path'] = '{}/{}_{}'.format(
        args['save_model_path'], args['model_type'], args['embedding_dim']
    )

    # Initialize neural architecture and optimizer to use
    if args['model_type'] == "TinyEmbedFFNN" and not args['sparse']:
        model = TinyEmbedFFNN(feature_dict, device, **args)
    elif args['model_type'] == "SparseLinear":
        model = SparseLinear(len(feature_dict))
    elif args['model_type'] == "SparseFFNN":
        model = SparseFFNN(len(feature_dict))
    elif args['model_type'] == "LargeEmbedFFNN":
        model = LargeEmbedFFNN(feature_dict, device, **args)
    elif args['model_type'] == "SmallEmbedFFNN":
        model = SmallEmbedFFNN(feature_dict, device, **args)
    elif args['model_type'] == "CrossNetwork":
        model = CrossNetwork(feature_dict, device, **args)
    else:
        raise NotImplementedError()

    if args["enable_cuda"] and torch.cuda.is_available(): model.to(device)

    start_epoch = 0
    optim_checkpoint = None
    if args['resume'] is not None:
        checkpoint = torch.load(args['resume'])
        model.load_state_dict(checkpoint['model'])
        optim_checkpoint = checkpoint['optimizer']
        start_epoch = checkpoint['epoch']
        logging.info("Resuming from model {}. Start at epoch: {}".format(args['resume'], start_epoch))

    n_params = sum([np.prod(par.size()) for par in model.parameters() if par.requires_grad])

    optimizer = torch.optim.SGD(model.parameters(), lr=args["learning_rate"], weight_decay=args['weight_decay'], momentum=0.9)
    if optim_checkpoint is not None:
        optimizer.load_state_dict(optim_checkpoint)
    logging.info("Initialized model and optimizer. Number of parameters: {}".format(n_params))

    if args['mode'] == 'train':
        train(model, optimizer, feature_dict, start_epoch, device, **args)
    else:
        run_test_set(model=model, test_filename=args['test'],
                     feature_dict=feature_dict, device=device, **args)
