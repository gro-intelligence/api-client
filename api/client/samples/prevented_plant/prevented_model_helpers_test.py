class planting_model_helpers(object):
    # Given weekly data of shape (num_weeks, some_data)
    # returns an array of shape (num_years, 52, some_data)
    #
    # start_year should be year (absolute, i.e. 2011) you want output array indexing to start at
    # num_years should be number of years from then you want outputted (don't exceed available data), (i.e. 2011 + 5 = 2016)
    # epoch gives the date weekly_data starts being available (i.e. the starting monday of the first week)

    @staticmethod
    def get_yearly(weekly_data, start_year, num_years, epoch):

        assert(len(weekly_data.shape) == 2)

        yearly_output = []

        for year_idx in range(num_years):
            first_day = datetime.date(start_year + year_idx, 1, 1)
            first_weekday = first_day.weekday()
            start_date = first_day - datetime.timedelta(first_weekday) if (
                        first_weekday <= 3) else first_day + datetime.timedelta(6 - first_weekday + 1)
            start_week_idx = (start_date - epoch).days // 7
            pre_pad = 0 if 0 - start_week_idx < 0 else 0 - start_week_idx
            post_pad = 0 if (start_week_idx + 52 - len(weekly_data)) < 0 else (start_week_idx + 52 - len(weekly_data))
            weekly_data_for_year = np.lib.pad(weekly_data[start_week_idx:start_week_idx + 52], (pre_pad, post_pad),
                                              'constant', constant_values=(np.nan))
            yearly_output.append(weekly_data_for_year)

        return np.array(yearly_output)
