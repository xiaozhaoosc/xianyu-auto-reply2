package com.xyun.platform.server.product;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyCatalogItem;
import com.xyun.platform.common.entity.XyProductMaterial;
import com.xyun.platform.common.entity.XyPublishAddress;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 商品管理 API — 商品目录、素材库、地址池
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ProductController {

    private final ProductService productService;

    // ==================== 商品目录 ====================

    /** 商品目录列表 */
    @GetMapping("/catalog-items")
    public ApiResult<Page<XyCatalogItem>> listCatalogItems(
            @RequestParam(defaultValue = "1") int current,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) Long accountId) {
        return productService.listCatalogItems(current, size, accountId);
    }

    /** 商品详情 */
    @GetMapping("/catalog-items/{id}")
    public ApiResult<XyCatalogItem> getCatalogItem(@PathVariable Long id) {
        return productService.getCatalogItem(id);
    }

    /** 添加商品 */
    @PostMapping("/catalog-items")
    public ApiResult<XyCatalogItem> addCatalogItem(@RequestBody XyCatalogItem item) {
        return productService.addCatalogItem(item);
    }

    /** 删除商品 */
    @DeleteMapping("/catalog-items/{id}")
    public ApiResult<Void> deleteCatalogItem(@PathVariable Long id) {
        return productService.deleteCatalogItem(id);
    }

    // ==================== 素材库 ====================

    /** 素材库列表 */
    @GetMapping("/product-materials")
    public ApiResult<Page<XyProductMaterial>> listProductMaterials(
            @RequestParam(defaultValue = "1") int current,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) Long userId) {
        return productService.listProductMaterials(current, size, userId);
    }

    /** 创建素材 */
    @PostMapping("/product-materials")
    public ApiResult<XyProductMaterial> createProductMaterial(@RequestBody XyProductMaterial material) {
        return productService.createProductMaterial(material);
    }

    /** 更新素材 */
    @PutMapping("/product-materials/{id}")
    public ApiResult<XyProductMaterial> updateProductMaterial(
            @PathVariable Long id, @RequestBody XyProductMaterial material) {
        return productService.updateProductMaterial(id, material);
    }

    /** 删除素材 */
    @DeleteMapping("/product-materials/{id}")
    public ApiResult<Void> deleteProductMaterial(@PathVariable Long id) {
        return productService.deleteProductMaterial(id);
    }

    // ==================== 地址池 ====================

    /** 地址池列表 */
    @GetMapping("/publish-addresses")
    public ApiResult<Page<XyPublishAddress>> listPublishAddresses(
            @RequestParam(defaultValue = "1") int current,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String accountId) {
        return productService.listPublishAddresses(current, size, accountId);
    }

    /** 添加地址 */
    @PostMapping("/publish-addresses")
    public ApiResult<XyPublishAddress> addPublishAddress(@RequestBody XyPublishAddress address) {
        return productService.addPublishAddress(address);
    }

    /** 更新地址 */
    @PutMapping("/publish-addresses/{id}")
    public ApiResult<XyPublishAddress> updatePublishAddress(
            @PathVariable Long id, @RequestBody XyPublishAddress address) {
        return productService.updatePublishAddress(id, address);
    }

    /** 删除地址 */
    @DeleteMapping("/publish-addresses/{id}")
    public ApiResult<Void> deletePublishAddress(@PathVariable Long id) {
        return productService.deletePublishAddress(id);
    }
}
