from lib.ca_elements.core import CAFile


if __name__ == "__main__":
    test = CAFile("test2.ca")
    layer = test.rootlayer.findlayer("KANYE WEST")
    layer.name = "THIS WAS EDITED"
    test.write_file("test3.ca")
