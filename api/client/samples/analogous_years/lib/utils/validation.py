def top_k(dataframe, column_name, k = 5):
    time_period_list = []
    for i in range(2, 2+k):
        time_period_list.append(
            dataframe[dataframe[column_name] == i].index.tolist()[0])
    return set(time_period_list)
