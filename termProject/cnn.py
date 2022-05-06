import argparse
import csv
import os
from pathlib import Path

import matplotlib.pyplot as plt                                     # type: ignore
from utils.animate import Loader                                    # type: ignore
from torchvision import datasets, transforms                        # type: ignore
from torch.utils.data import DataLoader                             # type: ignore
import torch.nn as nn                                               # type: ignore
import torch.nn.functional as F                                     # type: ignore
import torch.optim as optim                                         # type: ignore
import torch                                                        # type: ignore
from tqdm import tqdm                                               # type: ignore
from PIL import Image                                               # type: ignore


class Client:
    def __init__(self, dir: str) -> None:
        self.dir = dir
        self.batch_size_train = 64
        self.batch_size_val = 1000
        self.n_epochs = 80
        self.learning_rate = 0.0013
        self.momentum = 0.5
    
    # load the data from the folders
    def get_data(self):
        transform = transforms.Compose([transforms.Grayscale(num_output_channels=1),transforms.Resize((40,114)),transforms.ToTensor(),transforms.Normalize((0.5,), (0.5,)),])

        # ImageFolder automatically assign labels to imgs using the name of their folder
        train_set = datasets.ImageFolder(self.dir + '/train',transform=transform)
        val_set = datasets.ImageFolder(self.dir + '/val',transform=transform)
        
        img, label = train_set[0]
        print("my input data size: ", img.shape)

        train_loader = DataLoader(train_set, batch_size=self.batch_size_train, shuffle=True)
        val_loader = DataLoader(val_set, batch_size=self.batch_size_val, shuffle=True)

        return train_loader, val_loader
    
    # visualize first 5 images
    def train_imshow(self, train_loader):
        classes = ('1', '10', '2', '3', '4', '5', '6', '7', '8', '9') # Defining the classes we have
        dataiter = iter(train_loader)
        images, labels = dataiter.next()
        fig, axes = plt.subplots(figsize=(20, 8), ncols=5)
        for i in range(5):
            ax = axes[i]
            ax.imshow(images[i].permute(1,2,0).squeeze()) 
            ax.title.set_text(' '.join('%5s' % classes[labels[i]]))
        plt.show()
        
    def test(self, model, test_loader, device, verbosity):
        # evaluation, freeze 
        model.eval()
        total_num = 0
        total_correct = 0
        with torch.no_grad():
            for _, (data, target) in enumerate(test_loader):
                data = data.to(device)
                target = target.to(device)
                
                predict_one_hot = model(data)
                
                _, predict_label = torch.max(predict_one_hot, 1)
                if verbosity==1:
                    print("llllll",predict_label)
                total_correct += (predict_label == target).sum().item()
                total_num += target.size(0)
            
        return (total_correct / total_num)

    # define the training procedure
    def train(self, model, train_loader, test_loader, device, verbosity, num_epoch='', learning_rate='', momentum=''):
        train_losses = []
        if not num_epoch:
            num_epoch=self.n_epochs
        if not learning_rate:
            learning_rate=self.learning_rate
        if not momentum:
            momentum=self.momentum
        # 1, define optimizer
        # "TODO: try different optimizer"
        optimizer = optim.Adam(network.parameters(), lr=learning_rate)

        for epoch in tqdm(range(num_epoch)):
            # train the model
            model.train()
            for i, (data, target) in enumerate(train_loader):
                
                data = data.to(device)
                target = target.to(device)
                optimizer.zero_grad()
                
                # 2, forward
                output = network(data)
                
                # 3, calculate the loss
                "TODO: try use cross entropy loss instead "
                loss = F.nll_loss(output, target)
                
                # 4, backward
                loss.backward()
                optimizer.step()
            # evaluate the accuracy on test data for each epoch
            accuracy = self.test(model, test_loader, device, verbosity)
            if verbosity==1:
                print('accuracy', accuracy)
                print("loss: ",loss)
        
        
# define the cnn model
class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d(0.2)
        self.fc1 = nn.Linear(3500, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 20*7*25) # 220*37*111
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, -1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Handwriting Recognition CNN")
    parser.add_argument("--run", "-r", action="store_true")
    parser.add_argument("--save", "-s", action="store_true")
    parser.add_argument("--eval", "-t", action="store_true")
    parser.add_argument("--epochs", metavar='N', type=int)
    parser.add_argument("--learn_rate", metavar='N', type=int)
    parser.add_argument("--dir", "-d", metavar='N', type=str)
    parser.add_argument("--verbosity", metavar='N', type=int)
    args = parser.parse_args()
    
    if args.eval:
        client = Client(dir=args.dir[0] if  args.dir else './imgs_classified_split')
        train_loader, val_loader = client.get_data()
        device0 = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        network = CNN().to(device0)
        client.train(model=network, train_loader=train_loader, 
                    test_loader=val_loader, device=device0,
                    num_epoch=args.epochs[0] if args.epochs else 80,
                    learning_rate=args.learn_rate[0] if args.learn_rate else 0.0013,
                    verbosity=args.verbosity[0] if args.verbosity else 1)
    if args.save:
        # save an eval run as a final model
        if not os.path.exists('final_model.h5'):
            line = '#'*50
            print(f'{line}\nSaving a Copy of CNN Model\n{line}\nepochs = {args.epochs if args.epochs else 80}\n\n')
            loader = Loader("Running Model To Save...", "All done!", 0.05).start()          
            client = Client(dir=args.dir[0] if  args.dir else './imgs_classified_split')
            train_loader, val_loader = client.get_data()
            device0 = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
            network = CNN().to(device0)
            client.train(model=network, train_loader=train_loader, 
                        test_loader=val_loader, device=device0,
                        num_epoch=args.epochs if args.epochs else 80,
                        learning_rate=args.learn_rate[0] if args.learn_rate else 0.0013,
                        verbosity=args.verbosity[0] if args.verbosity else 1)
            torch.save(network.state_dict(), './final_model.h5')
            loader.stop()
        else:
            print(f'\nFinal Model already found, no need to save!\n\n\nEnter the cmd:   python main.py -r')
    if args.run:
        network = CNN()
        network.load_state_dict(torch.load('./final_model.h5'))
        # Create the preprocessing transformation here
        transform = transforms.Compose([transforms.Grayscale(num_output_channels=1),transforms.Resize((40,114)),transforms.ToTensor(),transforms.Normalize((0.5,), (0.5,)),])
        if args.dir:
            line = '#'*50
            print(f'{line}\nLoading Model...\n{line}\nUsing dir provided:  {args.dir}\n\n')
            final_results = []
            loader = Loader("Predicting and Writing...", "All done!", 0.05).start()          

            for root, dirs, files in os.walk(args.dir, topdown=False):
                # build train and val data sets
                for name in files:
                    cur_path = (os.path.join(root, name))
                    if not cur_path[len(cur_path)-1][0] == '.':
                        # load your image(s)
                        img = Image.open(os.getcwd() + '/' + os.path.join(root, name))
                        # Transform
                        input = transform(img)
                        # unsqueeze batch dimension, in case you are dealing with a single image
                        input = input.unsqueeze(0)
                        # Set model to eval
                        network.eval()
                        # Get prediction
                        output = network(input)
                        pred = torch.max(output.data, 1).indices
                        final_results.append({'img':name, 'label':pred[0].item()})
            keys = final_results[0].keys()
            with open('./results.csv', 'w', newline=None) as output_file:
                dict_writer = csv.DictWriter(output_file, keys)
                dict_writer.writeheader()
                dict_writer.writerows(final_results)
            loader.stop()
        else:
            line = '#'*50
            print(f'{line}\nNO GIVEN DIRECTORY\n{line}\nPlease provide a directory of images, like so:\n\npython3.* main.py --run/-r --dir/-d dir_name\n\n')

        
        
# matplot lib below
        
    
# # @timer
# def summarize_diagnostics(histories):
#     ''' plot diagnostic learning curves. '''
#     for i in range(len(histories)):
#         # plot loss
#         plt.subplot(2, 1, 1)
#         plt.title('Cross Entropy Loss')
#         plt.plot(histories[i].history['loss'], color='blue', label='train')
#         plt.plot(histories[i].history['val_loss'], color='orange', label='test')
#         # plot accuracy
#         plt.subplot(2, 1, 2)
#         plt.title('Classification Accuracy')
#         plt.plot(histories[i].history['accuracy'], color='blue', label='train')
#         plt.plot(histories[i].history['val_accuracy'], color='orange', label='test')
#     plt.show()
    
# # @timer
# def summarize_performance(scores):
#     ''' summarize model performance. '''
#     # print summary
#     print('Accuracy: mean=%.3f std=%.3f, n=%d' % (mean(scores)*100, std(scores)*100, len(scores)))
#     # box and whisker plots of results
#     plt.boxplot(scores)
#     plt.show()

# def visualize(client, train_loader) -> None:
#     client.train_imshow(train_loader)
#     for i, (images, labels) in enumerate(train_loader):
#         print(images.shape)
#         break
