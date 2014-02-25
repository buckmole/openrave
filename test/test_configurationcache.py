# -*- coding: utf-8 -*-
# Copyright (C) 2011-2012 Rosen Diankov <rosen.diankov@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from common_test_openrave import *

import imp

class TestConfigurationCache(EnvironmentSetup):
    def setup(self):
        EnvironmentSetup.setup(self)
        # find out where configurationcache is installed
        cachepath = None
        for path, info in RaveGetPluginInfo():
            pathdir, pathname = os.path.split(path)
            if pathname.find('openravepy_configurationcache') >= 0:
                cachepath = path
                break
        assert(cachepath is not None)
        self.openravepy_configurationcache = imp.load_dynamic('openravepy_configurationcache',cachepath)
        
    def test_insertandquery(self):
        self.LoadEnv('data/lab1.env.xml')
        env=self.env
        robot=env.GetRobots()[0]
        robot.SetActiveDOFs(range(7))
        cache=self.openravepy_configurationcache.ConfigurationCache(robot)
        
        values = robot.GetActiveDOFValues()
        inserted = cache.InsertConfiguration(values, None)
        assert(inserted and cache.GetNumNodes()==1)
        values[1] = pi/2
        inserted=cache.InsertConfiguration(values, None)
        assert(inserted and cache.GetNumNodes()>=2)
        assert(cache.Validate())
                
        values[1] = pi/2-0.0001
        robot.SetActiveDOFValues(values)
        ret, closestdist, collisioninfo = cache.CheckCollision(values)
        assert(ret==0)

        originalvalues = array([0,pi/2,0,pi/6,0,0,0])
        
        sampler = RaveCreateSpaceSampler(env, u'MT19937')
        sampler.SetSpaceDOF(robot.GetActiveDOF())
        report=CollisionReport()
        
        with env:
            for iter in range(0, 10000):
                robot.SetActiveDOFValues(originalvalues + 0.05*(sampler.SampleSequence(SampleDataType.Real,1)-0.5))
                samplevalues = robot.GetActiveDOFValues()
                incollision = env.CheckCollision(robot, report=report)
                inserted = cache.InsertConfiguration(samplevalues, report if incollision else None)
            self.log.info('cache has %d nodes', cache.GetNumNodes())
            assert(cache.Validate())
        
        with env:
            numspurious = 0
            nummisses = 0
            numtests = 1000
            collisiontimes = []
            cachetimes = []
            for iter in range(0, numtests):
                robot.SetActiveDOFValues(originalvalues + 0.05*(sampler.SampleSequence(SampleDataType.Real,1)-0.5))
                samplevalues = robot.GetActiveDOFValues()
                starttime=time.time()
                ret, closestdist, collisioninfo = cache.CheckCollision(samplevalues)
                midtime=time.time()
                incollision = env.CheckCollision(robot, report=report)
                endtime=time.time()
                cachetimes.append(midtime-starttime)
                collisiontimes.append(endtime-midtime)
                if ret != -1:
                    assert(closestdist <= 1)
                    # might give spurious collision since cache is being conservative
                    if incollision != ret:
                        if ret == 1:
                            numspurious += 1
                        else:
                            # unexpected freespace
                            assert(0)
                else:
                    nummisses += 1
            self.log.info('num spurious colisions=%d/%d, num misses = %d/%d, meancache=%fs, meancollision=%fs', numspurious, numtests, nummisses, numtests, mean(cachetimes), mean(collisiontimes))
        assert(float(numspurious)/float(numtests)<=0.06)
        assert(float(nummisses)/float(numtests)>0.1) # space is pretty big
        assert(mean(cachetimes) < mean(collisiontimes)) # caching should be faster
        
    def test_cacheplan(self):
        pass
