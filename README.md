## CMSIS device headers for STM32

This folder includes the CMSIS device headers for all STM32 devices.
The files located here are part of the `STM32Cube` libraries and can be found inside the `STM32Cube*/Drivers/CMSIS/Device/ST/STM32F*xx/Include` folder.

The files are copied and modified by converting all line endings from Windows to Unix style and removing all trailing whitespace (see `post_script.sh`).

Here is the list of the current device header version and release date as well as the Cube release version in braces:

- [L0: v1.9.0 created 26-October-2018](https://github.com/STMicroelectronics/STM32CubeL0)
- [L1: v2.3.0 created 05-April-2019](https://github.com/STMicroelectronics/STM32CubeL1)
- [L4: v1.6.0 created 22-November-2019](https://github.com/STMicroelectronics/STM32CubeL4)
- [F0: v2.3.4 created 12-September-2019](https://github.com/STMicroelectronics/STM32CubeF0)
- [F1: v4.3.1 created 26-June-2019](https://github.com/STMicroelectronics/STM32CubeF1)
- [F2: v2.2.2 created 26-June-2019](https://github.com/STMicroelectronics/STM32CubeF2)
- [F3: v2.3.4 created 12-September-2019](https://github.com/STMicroelectronics/STM32CubeF3)
- [F4: v2.6.4 created 06-December-2019](https://github.com/STMicroelectronics/STM32CubeF4)
- [F7: v1.2.4 created 08-February-2019](https://github.com/STMicroelectronics/STM32CubeF7)
- [G0: v1.3.0 created 25-June-2019](https://github.com/STMicroelectronics/STM32CubeG0)
- [G4: v1.1.0 created 28-June-2019](https://github.com/STMicroelectronics/STM32CubeG4)
- [H7: v1.7.0 created 06-December-2019](https://github.com/STMicroelectronics/STM32CubeH7)
- [WB: v1.2.0 created 11-September-2019](https://github.com/STMicroelectronics/STM32CubeWB)

The Travis CI integration checks these versions daily and will update them automatically.
However, when our manual patches fail to apply, the CI will fail: [![](https://travis-ci.org/modm-io/cmsis-header-stm32.svg?branch=master)](https://travis-ci.org/modm-io/cmsis-header-stm32)

The ST header files in this directory are available under the BSD 3-Clause License:
```
COPYRIGHT(c) {year} STMicroelectronics

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
  1. Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright notice,
     this list of conditions and the following disclaimer in the documentation
     and/or other materials provided with the distribution.
  3. Neither the name of STMicroelectronics nor the names of its contributors
     may be used to endorse or promote products derived from this software
     without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```
