import { Shell } from './Shell';
import { type TormentaPowerStatic } from './TormentaPowerStatic';
export declare class TormentaPowers {
    static readonly map: {
        shell: typeof Shell;
    };
    static getAll(): TormentaPowerStatic[];
}
