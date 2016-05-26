# Cognitive Atlas Voxel Visualization

### Running

Without Docker

      cd cogatcloud
      python index.py

Then go to http://127.0.0.1:5000/ in your browser.


With Docker

      git clone http://www.github.com/vsoch/cogatcloud
      cd cogatcloud
      docker-compose up -d

You will then need to get the ipaddress of your docker web:

      docker inspect cogatcloud_web_1 |grep "IPAddress"

And it should be repeated twice (will have better solution for this). Then go to ${IPADDRESS}:5000 in your browser.



### About the Visualization
The visualization allows you to see the cognitive concepts that are associated with each voxel (a spatial location indicated by an x,y,z coordinate) in the brain. The size of the cognitive concepts represents the contribution to the model for that voxel. See the info icon in the upper left of the visualization to learn more.
