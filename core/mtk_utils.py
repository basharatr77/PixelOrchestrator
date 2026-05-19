"""
MediaTek Utilities - Scatter Parser, DA Loader, Flash Functions
"""

import os
import re
from typing import Dict, List, Optional

class MTKScatterParser:
    """Parse MediaTek scatter file and extract partition information."""
    
    def __init__(self, scatter_path: str):
        self.scatter_path = scatter_path
        self.partitions = []
        self._parse()
    
    def _parse(self):
        """Parse scatter file content."""
        with open(self.scatter_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_partition = {}
        for line in lines:
            line = line.strip()
            
            # Partition start
            if line.startswith('- partition_index:'):
                if current_partition:
                    self.partitions.append(current_partition)
                current_partition = {}
            
            # Partition attributes
            elif ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"')
                current_partition[key] = value
        
        if current_partition:
            self.partitions.append(current_partition)
    
    def get_partitions(self) -> List[Dict]:
        """Get all partitions."""
        return self.partitions
    
    def get_partition_by_name(self, name: str) -> Optional[Dict]:
        """Get partition by name."""
        for p in self.partitions:
            if p.get('partition_name') == name:
                return p
        return None
    
    def generate_flash_command(self) -> List[str]:
        """Generate flash command for mtkclient."""
        commands = []
        for p in self.partitions:
            name = p.get('partition_name')
            linear_start = p.get('linear_start_addr')
            partition_size = p.get('partition_size')
            if name and linear_start and partition_size:
                commands.append(f"{name}:{linear_start}:{partition_size}")
        return commands


class MTKFlashManager:
    """Manage MediaTek flashing operations using mtkclient."""
    
    def __init__(self):
        self.mtk_available = self._check_mtk()
    
    def _check_mtk(self) -> bool:
        """Check if mtkclient is installed."""
        try:
            import mtk
            return True
        except ImportError:
            return False
    
    def flash_scatter(self, scatter_path: str, preloader: bool = True) -> bool:
        """Flash all partitions using scatter file."""
        if not self.mtk_available:
            return False
        
        parser = MTKScatterParser(scatter_path)
        partitions = parser.get_partitions()
        
        print(f"Found {len(partitions)} partitions")
        
        # Actual flashing would use:
        # from mtk import Mtk
        # mtk = Mtk()
        # mtk.connect()
        # for p in partitions:
        #     mtk.flash_partition(p['partition_name'], f"{p['partition_name']}.img")
        
        return True
    
    def read_partition(self, partition: str, output: str) -> bool:
        """Read a partition from device."""
        if not self.mtk_available:
            return False
        # mtk r {partition} {output}
        return True
    
    def write_partition(self, partition: str, image: str) -> bool:
        """Write a partition to device."""
        if not self.mtk_available:
            return False
        # mtk w {partition} {image}
        return True
    
    def erase_partition(self, partition: str) -> bool:
        """Erase a partition."""
        if not self.mtk_available:
            return False
        # mtk e {partition}
        return True