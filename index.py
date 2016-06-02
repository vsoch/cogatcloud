from flask import Flask, render_template
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import cStringIO
import random
import numpy
import pandas
import pickle

# SERVER CONFIGURATION ##############################################
class CogatServer(Flask):

    def __init__(self, *args, **kwargs):
            super(CogatServer, self).__init__(*args, **kwargs)

            # load data on start of application
            self.df = pandas.read_pickle("data/regression_params.pkl")
            self.images = pandas.read_csv("data/contrast_defined_images_filtered.tsv",sep="\t",index_col="image_id")
            self.Y = pandas.read_csv("data/images_contrasts_df.tsv",sep="\t",index_col=0)
            self.lookup = pandas.read_csv("data/cogatlas_concepts.tsv",sep="\t",index_col=0)
            self.regions = pandas.read_csv("data/aal_4mm_region_coords.tsv",sep="\t",index_col=0)
            self.region_lookup = pandas.read_pickle("data/aal_4mm_region_lookup.pkl")

            # D3 specific variables
            self.width = 1200
            self.height = 1000
            self.padding = 12
            self.maxRadius = 12
          
            # Image data
            self.X = pickle.load(open("data/images_df.pkl","rb"))
            # value will be radius, we don't want negative values
            self.radius = self.X + self.X.min().abs()

            # Pairwise spatial similarity
            self.spatial = pandas.read_csv("data/contrast_defined_images_pearsonpd_similarity.tsv",sep="\t",index_col=0)

app = CogatServer(__name__)

# Global variables for app

### Helper Functions
def make_node(concept,tagged_image,v):
  image = app.images.loc[tagged_image]
  classes = " ".join(app.Y.loc[tagged_image][app.Y.loc[tagged_image]==1].index.tolist())
  return {
    "radius": app.radius.loc[tagged_image,v],
    "concept": concept,
    "concept_name":app.lookup.name[app.lookup.id==concept].tolist()[0],
    "classes":classes,
    "contrast": image.cognitive_contrast_cogatlas,
    "task": image.cognitive_paradigm_cogatlas,
    "collection": image.collection_id,
    "thumbnail": image.thumbnail,
    "value": app.X.loc[tagged_image,v],
    "uid":tagged_image
   }

def get_lookup():
    lookup = dict()
    for row in app.lookup.iterrows():
        lookup[row[1].id] = row[1]["name"] #cannot be .name
    return lookup

def random_colors(concepts):
    '''Generate N random colors'''
    colors = {}
    for x in range(len(concepts)):
        concept = concepts[x]
        r = lambda: random.randint(0,255)
        colors[concept] = '#%02X%02X%02X' % (r(),r(),r())
    return colors


@app.route("/<v>")
def voxel(v,name):

    voxel_idx = int(v)

    # Prepare variables
    regparams = app.df.loc[voxel_idx]

    # Generate a lookup by concept name
    lookup = get_lookup()

    # We are only interested in nonzero concepts
    regparams = pandas.DataFrame(regparams[regparams!=0])
    concepts = regparams.index.tolist()
    colors = random_colors(concepts)

    regparams["key"] = [lookup[x] for x in regparams.index]
    regparams["color"] = [colors[x] for x in regparams.index]
    regparams.columns = ['value', 'key', 'color']

    # Generate a word cloud image, take regression params into account
    scaled = (regparams['value'].abs()*1000).copy()
    text = []
    for k,v in scaled.iteritems():
        multiply_by = int(v)
        string = [regparams.loc[k]['key'].replace(" ","_")] * multiply_by
        text = text + string

    text =  " ".join(text)
    regparams = regparams.to_json(orient="records")

    # Min and max values for the color scale
    min_voxel = app.X.loc[:,voxel_idx].min()
    max_voxel = app.X.loc[:,voxel_idx].max()

    # We will let the user select a voxel location based on region
    regions = app.regions.to_dict(orient="records")
    
    wordcloud = WordCloud(max_font_size=100, width=app.width, height=app.height,
                          relative_scaling=1.0, background_color="white").generate(text)

    # Remove "_" in words
    words = []
    for tup in wordcloud.words_:
        words.append((tup[0].replace("_"," "),tup[1]))
    wordcloud.words_ = words

    layout = []
    for tup in wordcloud.layout_:
        newtup = ((tup[0][0].replace("_"," "),tup[0][1]),
                  tup[1],
                  tup[2],
                  tup[3],
                  tup[4])
        layout.append(newtup)
    wordcloud.layout_ = layout

    plt.imshow(wordcloud)
    plt.axis("off")
    sio = cStringIO.StringIO()
    plt.savefig(sio, format="png")
    png_data = sio.getvalue().encode("base64").strip()

    return render_template("cloud.html",regparams=regparams,
                                        min=app.df.loc[voxel_idx].min(),
                                        max=app.df.loc[voxel_idx].max(),
                                        width=app.width,
                                        min_voxel=min_voxel,
                                        max_voxel=max_voxel,
                                        height=app.height,
                                        padding=app.padding,
                                        radius=app.radius,
                                        maxRadius=app.maxRadius,
                                        lookup=lookup,
                                        colors=colors,
                                        png_data=png_data,
                                        voxel=voxel_idx,
                                        regions=regions,
                                        region_name=name)

@app.route("/")
def index():
    # Select a random region
    name = numpy.random.choice(app.regions.name.tolist(),1)[0]
    return region(name)
    

@app.route("/region/<name>")
def region(name):

    # Look up the value of the region
    value = app.regions.value[app.regions.name==name].tolist()[0]
    
    # Select a voxel coordinate at random
    voxel_idx = numpy.random.choice(app.region_lookup.index[app.region_lookup.aal == value],1)[0]

    return voxel(voxel_idx,name=name)

if __name__ == "__main__":
    app.debug = True
    app.run()

