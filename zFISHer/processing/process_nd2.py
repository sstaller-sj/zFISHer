from nd2reader import ND2Reader


def nd2_metadata_processor(filepath) -> None:
        """
        Extract image capture metadata info from each file for analysis.

        Args:
        filepath (string): The filepath to pull metadata from.
        
        
        Returns:
            metadata_dict (dict): contains relevant metadata from input nd2 file. The dict keys are:
                - 'f_c_num' (int): The number of channels in the file.
                - 'f_z_num' (int): The number of z-slices in the file stack.
                - 'f_c_list' (list): A list of strings of each channel name in the file.
        """

        #FILE1
        with ND2Reader(filepath) as nd2_file:
            print(nd2_file.metadata)
            f_c_num = len(nd2_file.metadata['channels'])
            f_z_num = len(nd2_file)
            f_c_list = nd2_file.metadata['channels']

        
        metadata_dict = {
            'c_num' : f_c_num,
            'z_num' : f_z_num,
            'c_list' : f_c_list
            }

        return metadata_dict