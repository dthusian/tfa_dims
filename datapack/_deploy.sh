#!/bin/bash

cd "$(dirname "$0")"

rm -f datapack.zip
zip -r datapack.zip data pack.mcmeta
#cp datapack.zip ../run/world/datapacks/
cp datapack.zip "/home/dthusian/Documents/appdata/MultiMc-instances/1.21.10 Fabric/.minecraft/saves/dimtest/datapacks/" 