# Accuracy and limits

The pinned local profile uses VTracer 1.0.0-alpha.4 with `photo` segmentation and `pixel` fitting. In the maintained 1013×524 LECO reference it reached SSIM 0.9982763, PSNR 44.001786 dB, and MAE 0.912993 with 87,432 paths. These figures explain the fidelity choice but do not predict unrelated images.

High visual similarity and practical editability are different goals. Pixel fitting can preserve a supplied raster closely while producing hundreds of thousands of solid regions. PowerPoint must store and render every region as a separate object, so continuous-tone photography often becomes unusable when expanded natively.

Use native mode for bounded, hard-edged diagrams; light-native mode for continuous tones or over-budget traces; archive mode for maximum-fidelity SVG. Light-native output remains fully vector/native, but may reduce palette size, discard tiny regions, simplify curves, or trace a downsampled source. Scaling an SVG does not recreate source detail that was absent in the raster.
