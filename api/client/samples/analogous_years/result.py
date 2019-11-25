def result(dataframe, year=2019):
    '''
    :param dataframe: A dataframe of euclidean distance between two years beased on extracted features.
    :year: The year with respect to which we are trying to find the distance
    :return: The closest years to each given year
    '''
    year = str(year)[-2:]
    if year[0] == '0':
        year = year[1]
    year = int(year)
    return dataframe[year].sort_values()



