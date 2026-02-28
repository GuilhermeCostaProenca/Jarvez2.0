import type { Attributes } from '../Sheet/Attributes';
import type { Level } from '../Sheet/Level';
import { PointsMaxCalculator } from './PointsMaxCalculator';
export declare class PointsMaxCalculatorFactory {
    static make(attributes: Attributes, level: Level): PointsMaxCalculator;
}
