import numpy as np
import pandas as pd 
from pandas import read_csv
from pandas.plotting import autocorrelation_plot
from matplotlib import pyplot
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from statsmodels.tsa.arima_model import ARIMA
import datetime 
import sys
import argparse

COUNTRY_LABEL = 'Country/Region'
GRAPH_FORMATS = ['-','o--','^-.',':','^-','o:','*--']

class VirusSeries:

    def __init__(self, file_path, country_names):
        """
        :param file_path: the file on disk where time series data is stored.
        :param country_names: a vector with the names for which we want to extract data 
        """
        self.countries=country_names
        self.dates=[]
        self.__load(file_path)
        self.log = False
        self.models = {}

    def __load(self, file_path):
        """
        Loads the dataset and transforms it into timeseries
        :param file_path: the file on disk where time series data is stored.
        """
        self.series = read_csv(file_path, header=0)
        self.series = self.__extract_series_per_country(self.countries).transpose().iloc[1:]
        self.series.index.names = ['Date']
        self.series.index = pd.to_datetime(self.series.index)
        self.series.columns = self.countries 

    def __extract_series_per_country(self, countries):
        """
        Extracts the timeseries for the requested countries
        :param countries: list of countries to process and visualize
        """
        frames = []
        for country in countries:
            country_series = self.series.loc[self.series[COUNTRY_LABEL] == country]
            frames.append(country_series)
        df = pd.concat(frames)
        mask = [False, True, False, False]
        mask = mask + [True for i in range(4, len(list(df)))]
        return df.iloc[:,mask]

    def slice(self, start_date, end_date = None):
        """
        Returns a slice of the matrix based on date predicates
        :param start_date: string representation of the start date of the requested range 
        :param end_date: string representation of the end date of the requested range. If end date is not provided,
                         we consider as end the maximum date that exists in the original data matrix 
        """

        if end_date is None:
            end_date = self.series.index[-1]
            print(end_date)
        self.series = self.series.loc[start_date:end_date]

    def plot(self):
        """
        Plots number of incidents vs time 
        """
        fig, ax = plt.subplots()
        ticklabels = [item.strftime('%b %d') for item in self.series.index]
        ax.xaxis.set_major_formatter(ticker.FixedFormatter(ticklabels))

        plt.ylabel('#Cases')
        i = 0
        for y in self.countries:
            plt.plot(ticklabels, self.series[y], GRAPH_FORMATS[i], label=y)
            i += 1
        ax.set_xticklabels(ticklabels, rotation='vertical', fontsize=10)
        plt.legend()
        plt.grid()
        if self.log:
            plt.yscale("log")
        plt.show()

    # Used to evaluate the lag parameter for the ARIMA model. A good lag seems to be 2
    def param_eval(self, country):
        country_series = self.series[country]
        autocorrelation_plot(country_series)
        plt.show()

    def predict(self, next_days):
        """
        Updates the series with predictions for the next days
        :param next_days: the number of days that should be considered for predictions
        """
        last_date = self.series.index[-1]
        for time in range(next_days):
            row = {}
            for c in self.countries:
                history = self.series[c]
                series = history.astype(float)
                model = ARIMA(series, order=(2,1,0))
                model_fit = model.fit()
                output = model_fit.forecast()
                row[c] = output[0][0]
            last_date = last_date + pd.DateOffset(1)
            self.series.loc[last_date] = row 


def extract_country_names(file_path):
    f = open(file_path, "r")
    countries = []
    for line in f.readlines():
        countries.append(line.split(",")[1])
    f.close()
    print(countries)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='COVID-19 historic data manipulation.')
    parser.add_argument("--file", help = "File path where data is stored")
    parser.add_argument("--all_countries", help = "Extracts available countries. Requires the --files property to be set", dest="all_countries", action="store_true")
    parser.add_argument("--countries", help = "List with countries to visualize", nargs='+')
    parser.add_argument("--log", help = "Plots data in log scale", dest="log", action="store_true")
    parser.add_argument("--days", help = "Number of days ahead for predictions", type=int)
    parser.add_argument("--start_date", help = "First date (y-m-d) of interest for plotting data.")
    parser.add_argument("--end_date", help = "Last date (y-m-d) of interest for plotting data. Requires the --start_end property to be set")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.all_countries:
        extract_country_names(args.file)
        sys.exit(0)
    
    if (args.file is not None) and (args.countries is not None):
        matrix = VirusSeries(args.file, args.countries)
    else:
        parser.print_help(sys.stderr)
        sys.exit(1)
            
    if args.start_date is not None:
        if args.end_date is not None:
            matrix.slice(args.start_date, args.end_date)
        else:
            matrix.slice(args.start_date)

    if args.log:
        matrix.log = True 

    if args.days is not None:
        matrix.predict(args.days)
        
    matrix.plot()



