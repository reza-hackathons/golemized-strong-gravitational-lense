# Strong gravitational lensing on golem
This projects is a simple distributed computing hack that tries to simulate some physical phenomena called gravitional lensing.  
## Output  
![](https://github.com/rezahsnz/golemized-strong-gravitational-lense/raw/main/galaxy.gif)

## Demo  
[https://youtu.be/IQ0Xz0PEWoY](https://youtu.be/IQ0Xz0PEWoY)

## More?  
The work is fully based on the work of [Prof. Adam Bolton](http://www.physics.utah.edu/~bolton/python_lens_demo/). In order to produce various lense effects open the `task_dispatcher.py` and change the `points` variables' parameters.    
`points = np.arange(0.001, 1.0, 0.005)`  
The default version creates 200 points and divides them into 20 groups of 10 parameters each. Then each Golem node is delegated to produce 10 frames for each group. Finally all 200 frames are downloaded to the `out` folder. To create a `gif` file do the following steps:  
- `sudo apt-get install imagemagick`
- `convert -delay 36 -loop 0 out/*.png animatedGIF.gif`
